import math
import typing
import discord
from discord.ext import commands

import console_app
import postgresql_interface as db
import q_industrialist_settings
import q_router_settings
import q_discord_settings


argv_prms = console_app.get_argv_prms(['corporation='])


class Database:
    def __init__(self,
                 market_groups: bool = False,
                 universe_categories: bool = False,
                 universe_groups: bool = False,
                 all_known_type_ids: bool = False,
                 blueprints: bool = False,
                 conveyor_best_formulas: bool = False,
                 conveyor_formulas: bool = False,
                 corporation_assets: bool = False,
                 corporation_blueprints: bool = False,
                 corporation_blueprints_undelivered: bool = False,
                 corporation_container_places: bool = False,
                 corporation_industry_jobs_active: bool = False,
                 corporation_industry_jobs_completed: bool = False,
                 corporation_orders_active: bool = False,
                 stations: bool = False,
                 conveyor_limits: bool = False,
                 conveyor_requirements: bool = False):
        # работа с параметрами командной строки, получение настроек запуска программы
        self.qidb: db.QIndustrialistDatabase = db.QIndustrialistDatabase(
            "discord",
            debug=argv_prms.get("verbose_mode", False))
        self.qidb.connect(q_industrialist_settings.g_database)
        self.qit: db.QSwaggerTranslator = db.QSwaggerTranslator(self.qidb)
        self.qid: db.QSwaggerDictionary = db.QSwaggerDictionary(self.qit)
        # загрузка справочников
        if market_groups:
            self.qid.load_market_groups()
        if universe_categories:
            self.qid.load_universe_categories()
        if universe_groups:
            self.qid.load_universe_groups()
        if all_known_type_ids:
            self.qid.load_all_known_type_ids()
        if blueprints:
            self.qid.load_blueprints()
        if conveyor_best_formulas:
            self.qid.load_conveyor_best_formulas()
        # загрузка информации, связанной с корпорациями
        if corporation_assets or \
           corporation_blueprints or \
           corporation_blueprints_undelivered or \
           corporation_container_places or \
           corporation_industry_jobs_active or \
           corporation_industry_jobs_completed or \
           corporation_orders_active or \
           stations:
            for corporation_name in argv_prms['corporation']:
                # публичные сведения (пилоты, структуры, станции, корпорации)
                corporation: db.QSwaggerCorporation = self.qid.load_corporation(corporation_name)
                # загрузка корпоративных ассетов
                if corporation_assets:
                    self.qid.load_corporation_assets(corporation, load_unknown_type_assets=True, load_asseted_blueprints=True)
                if corporation_blueprints:
                    self.qid.load_corporation_blueprints(corporation, load_unknown_type_blueprints=True)
                if corporation_blueprints_undelivered:
                    self.qid.load_corporation_blueprints_undelivered(corporation)
                if corporation_container_places:
                    self.qid.load_corporation_container_places(corporation)
                if corporation_industry_jobs_active:
                    self.qid.load_corporation_industry_jobs_active(corporation, load_unknown_type_blueprints=True)
                if corporation_industry_jobs_completed:
                    self.qid.load_corporation_industry_jobs_completed(corporation, load_unknown_type_blueprints=True)
                if corporation_orders_active:
                    self.qid.load_corporation_orders_active(corporation)
                if stations:
                    self.qid.load_corporation_stations(corporation)
        # загрузка настроек работы конвейера (редактируются online через php_interface)
        if conveyor_limits:
            self.qid.load_conveyor_limits()
        if conveyor_requirements:
            self.qid.load_conveyor_requirements()
        # загружаем сведения о станциях, которые есть в настройках маршрутизатора
        if stations:
            for r in q_router_settings.g_routes:
                station: typing.Optional[db.QSwaggerStation] = self.qid.load_station_by_name(r['station'])
                if not station:
                    raise Exception(f"Unable to load station by name: {r['station']}")
        # загрузка conveyor-формул после загрузки всех справочных и корпоративных данных (в т.ч. станций)
        if conveyor_formulas:
            self.qid.load_conveyor_formulas()

    def __del__(self):
        # отключаемся от сервера
        self.qid.disconnect_from_translator()
        del self.qit
        self.qidb.disconnect()
        del self.qidb


intents = discord.Intents.default()  # подключаем "Разрешения"
intents.message_content = True
help_command = commands.DefaultHelpCommand(no_category='Справка')
bot = commands.Bot(
    command_prefix='Q.',  # префикс
    intents=intents,  # интенты
    help_command=help_command)


class StatusCommands(commands.Cog, name="Проверка состояния"):
    @commands.command(pass_context=True, description='Проверка связи', help="Проверка связи")
    async def ping(self, ctx):
        await ctx.send(':ping_pong: pong')


class InformationCommands(commands.Cog, name="Получение сведений"):
    @staticmethod
    def strip_eve_online_type_name(name: str) -> str:
        return name.strip().removeprefix('*')

    @staticmethod
    def get_type_id_by_type_name(database: Database, name: str) -> typing.Optional[db.QSwaggerTypeId]:
        for type_id, item in database.qid.sde_type_ids.items():
            if not (item.name.lower() == name.lower()):
                continue
            return item
        return None

    @staticmethod
    def get_item_description(item: typing.Optional[db.QSwaggerTypeId]) -> typing.Optional[str]:
        description: typing.Optional[str] = None
        if item:
            if item.group:
                if item.group.category:
                    description = f'{item.group.category.name} / {item.group.name}'
                else:
                    description = f'{item.group.name}'
        return description

    @staticmethod
    def simplify_isk(isk: float) -> str:
        if isk < 1000000.0:
            return f'{isk:,.2f}'
        elif isk < 1000000000.0:
            return f'{math.ceil(isk):,d}'
        else:  # >= 1000000000
            return f'{math.ceil(round(isk, -3)):,d}'

    @commands.command(
        pass_context=True,
        description='Получить сведения о предмете (следует использовать кавычки для названий с'
                    'пробелами-разделителями).\nНапример:\nQ.item Tritanium\nQ.item "Acolyte II"\nQ.item 78576',
        help="Получить сведения о предмете")
    async def item(
            self,
            ctx: commands.Context,
            what: typing.Union[str, int] = commands.parameter(description='Название предмета либо его код')):
        database: Database = Database(
            market_groups=True,
            universe_categories=True,
            universe_groups=True,
            all_known_type_ids=True)
        paginator: typing.Optional[discord.ext.commands.Paginator] = None
        embed: typing.Optional[discord.Embed] = None
        item_name = self.strip_eve_online_type_name(what)
        if item_name.isdecimal():
            item: typing.Optional[db.QSwaggerTypeId] = database.qid.get_type_id(int(item_name))
        else:
            item: typing.Optional[db.QSwaggerTypeId] = self.get_type_id_by_type_name(database, item_name)
        if item:
            embed = discord.Embed(title=item.name, description=self.get_item_description(item), colour=0xF0C43F)
            embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
            if not item.published:
                embed.set_footer(text='Предмет отсутствует в игре')
            # ---
            paginator = discord.ext.commands.Paginator(prefix='', suffix='')
            paginator.add_line(f'`{item.name}`')
            paginator.add_line(f'* type_id = `{item.type_id}`')
            paginator.add_line(f'* published = {'yes' if item.published else 'no'}')
            if item.group_id:
                if item.group:
                    if item.group.category:
                        paginator.add_line(f'* category = {item.group.category.name} (`{item.group.category_id}`)')
                    else:
                        paginator.add_line(f'* category_id = `{item.group.category_id}`')
                    paginator.add_line(f'* group = {item.group.name} (`{item.group_id}`)')
                else:
                    paginator.add_line(f'* group_id = `{item.group_id}`')
            if item.market_group_id:
                if item.market_group:
                    if item.market_group.parent_id is None:
                        paginator.add_line(f'* market_group = {item.market_group.name} (`{item.market_group_id}`)')
                    else:
                        paginator.add_line('* market_groups:')
                        chain: typing.List[int] = database.qid.get_market_group_chain(item)
                        for market_group_id in reversed(chain):
                            g: db.QSwaggerMarketGroup = database.qid.get_market_group(market_group_id)
                            paginator.add_line(f'  {g.name} (`{g.group_id}`)')
                else:
                    paginator.add_line(f'* market_group_id = `{item.market_group_id}`')
            if item.meta_group_id:
                paginator.add_line(f'* meta_group_id = `{item.meta_group_id}`')
            if item.tech_level:
                paginator.add_line(f'* tech_level = `{item.tech_level}`')
            if item.volume:
                paginator.add_line(f'* volume = {item.volume:,.2f} m³')
            if item.capacity:
                paginator.add_line(f'* capacity = {item.capacity:,.2f} m³')
            if item.packaged_volume:
                paginator.add_line(f'* packaged_volume = {item.packaged_volume:,.2f} m³')
            if item.base_price:
                paginator.add_line(f'* base_price = {item.base_price:,.2f} ISK')
            if item.icon_id:
                paginator.add_line(f'* icon_id = `{item.icon_id}`')
        if paginator:
            for page in paginator.pages:
                await ctx.send(page, embed=embed)
                embed = None
        else:
            await ctx.send(f'Предмет с названием `{item_name}` не найден')
        del database

    @commands.command(
        pass_context=True,
        description='Получить сведения о местоположении имущества (следует использовать кавычки для названий с '
                    'пробелами-разделителями).\nНапример:\nQ.assets Venture',
        help="Получить сведения о местоположении имущества")
    async def assets(
            self,
            ctx: commands.Context,
            item_name: str = commands.parameter(description='Название предмета')):
        database: Database = Database(
            universe_categories=True,  # для вывода description в embed
            universe_groups=True,  # для вывода description в embed
            all_known_type_ids=True,
            corporation_assets=True,
            corporation_container_places=True,
            stations=True)
        paginator: typing.Optional[discord.ext.commands.Paginator] = None
        embed: typing.Optional[discord.Embed] = None
        item_name = self.strip_eve_online_type_name(item_name)
        item: typing.Optional[db.QSwaggerTypeId] = self.get_type_id_by_type_name(database, item_name)
        if item:
            embed = discord.Embed(title=item.name, description=self.get_item_description(item), colour=0xC85C70)
            embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
            # ---
            for corporation_id, corporation in database.qid.corporations.items():
                calculated: typing.Dict[typing.Optional[int],
                                        typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]]] = {}
                calculated_quantity: int = 0
                for a in corporation.assets.values():
                    if a.type_id == item.type_id:
                        calculated_quantity += a.quantity
                        s: typing.Dict[int, typing.List[db.QSwaggerCorporationAssetsItem]] = calculated.get(a.station_id)
                        if s:
                            c: typing.Optional[typing.List[db.QSwaggerCorporationAssetsItem]] = s.get(a.location_id)
                            if c:
                                c.append(a)
                            else:
                                s[a.location_id] = [a]
                        else:
                            calculated[a.station_id] = {}
                            calculated[a.station_id][a.location_id] = [a]
                if not calculated:
                    continue
                embed.add_field(
                    name=corporation.corporation_name,
                    value=f'{calculated_quantity:,d} шт',
                    inline=True)
                if not paginator:
                    paginator = discord.ext.commands.Paginator(prefix='', suffix='')
                    paginator.add_line(f'`{item.name}`')
                paginator.add_line(f'Имущество {corporation.corporation_name}:')
                for station_id, locations in calculated.items():
                    line_prefix: str = '* '
                    if station_id is not None:
                        s: typing.Optional[db.QSwaggerStation] = database.qid.get_station(station_id)
                        if s:
                            paginator.add_line(f'{line_prefix} `{s.station_name}`')
                        else:
                            paginator.add_line(f'{line_prefix} на станции `{station_id}`')
                        line_prefix = '  ' + line_prefix
                    for location_id, c in locations.items():
                        for a in [_ for _ in c if _.name is not None]:
                            location: db.QSwaggerCorporationAssetsItem = corporation.assets.get(location_id)
                            if location and location.name:
                                paginator.add_line(f'{line_prefix}`{a.name}` в `{location.name}` ({a.location_flag})')
                            else:
                                paginator.add_line(f'{line_prefix}`{a.name}` в `{location_id}` ({a.location_flag})')
                        quantity: int = sum([_.quantity for _ in c if _.name is None])
                        if quantity:
                            a: db.QSwaggerCorporationAssetsItem = c[0]
                            if location_id in corporation.container_ids:
                                container: db.QSwaggerCorporationAssetsItem = corporation.assets.get(location_id)
                                paginator.add_line(f'{line_prefix}{quantity:,d} шт в `{container.name}`')
                            else:
                                location: db.QSwaggerCorporationAssetsItem = corporation.assets.get(location_id)
                                if location and location.name:
                                    paginator.add_line(f'{line_prefix}{quantity:,d} шт в `{location.name}` ({a.location_flag})')
                                else:
                                    paginator.add_line(f'{line_prefix}{quantity:,d} шт в `{location_id}` ({a.location_flag})')
        if paginator:
            for page in paginator.pages:
                await ctx.send(page, embed=embed)
                embed = None
        elif item is None:
            await ctx.send(f'Предмет с названием `{item_name}` неизвестен')
        else:
            await ctx.send(f'Имущество с названием `{item_name}` не найдено', embed=embed)
        del database

    @commands.command(
        pass_context=True,
        description='Получить сведения о торговле предметом (следует использовать кавычки для названий с '
                    'пробелами-разделителями).\nНапример:\nQ.orders Skiff\nQ.orders "100mm Steel Plates II"',
        help="Получить сведения о торговле предметом")
    async def orders(
            self,
            ctx: commands.Context,
            product_name: str = commands.parameter(description='Название предмета')):
        database: Database = Database(
            all_known_type_ids=True,
            corporation_orders_active=True,
            stations=True)
        paginator: typing.Optional[discord.ext.commands.Paginator] = None
        general_embed: typing.Optional[discord.Embed] = None
        sell_embed: typing.Optional[discord.Embed] = None
        buy_embed: typing.Optional[discord.Embed] = None
        product_name = self.strip_eve_online_type_name(product_name)
        item: typing.Optional[db.QSwaggerTypeId] = self.get_type_id_by_type_name(database, product_name)
        if item:
            general_embed = discord.Embed(title=item.name, description=self.get_item_description(item), colour=0x2e6b4d)
            general_embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
            # ---
            sell_quantity: int = 0
            buy_quantity: int = 0
            for corporation_id, corporation in database.qid.corporations.items():
                calculated: typing.Dict[typing.Optional[int], typing.List[db.QSwaggerCorporationOrder]] = {}
                for o in corporation.orders.values():
                    if o.type_id == item.type_id:
                        if o.is_buy_order:
                            buy_quantity += o.volume_remain
                        else:
                            sell_quantity += o.volume_remain
                        s: typing.List[db.QSwaggerCorporationOrder] = calculated.get(o.location_id)
                        if s:
                            s.append(o)
                        else:
                            calculated[o.location_id] = [o]
                if not calculated:
                    continue
                if not paginator:
                    paginator = discord.ext.commands.Paginator(prefix='', suffix='')
                    paginator.add_line(f'`{item.name}`')
                if sell_quantity and not sell_embed:
                    sell_embed = discord.Embed(title=item.name, description='Продажа', colour=0x2e6b4d)
                    sell_embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
                if buy_quantity and not buy_embed:
                    buy_embed = discord.Embed(title=item.name, description='Покупка', colour=0x2e6b4d)
                    buy_embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
                key_station, key_corporation, key_buy = 0, 0, True
                for station_id, orders in calculated.items():
                    station_name: str = '(неизвестно)'
                    solar_system: str = '(неизвестно)'
                    if station_id is not None:
                        s: typing.Optional[db.QSwaggerStation] = database.qid.get_station(station_id)
                        if s:
                            station_name = s.station_name
                            solar_system = s.solar_system_name
                        else:
                            station_name = str(station_id)
                            solar_system = str(station_id)
                    for is_buy_order in [True, False]:
                        oo: typing.List[db.QSwaggerCorporationOrder] = [_ for _ in orders
                                                                        if _.is_buy_order == is_buy_order]
                        remain: int = sum([_.volume_remain for _ in oo])
                        if not remain:
                            continue
                        total: int = sum([_.volume_total for _ in oo])
                        is_multi_order: bool = len(oo) > 1
                        if key_station != station_id or \
                           key_corporation != corporation.corporation_id or\
                           key_buy != is_buy_order:
                            paginator.add_line(f'{'Закупка' if is_buy_order else 'Продажа'} '
                                               f'`{corporation.corporation_name}` в `{station_name}`:')
                            (buy_embed if is_buy_order else sell_embed).add_field(
                                name=solar_system,
                                value=f'{remain:,d} шт\n'
                                      f'остаток {100.0*remain/total:,.1f}%\n'
                                      f'`{sum([_.price * _.volume_remain for _ in oo])/remain:,.2f}` ISK',
                                inline=True)
                            key_station = station_id
                            key_corporation = corporation.corporation_id
                            key_buy = is_buy_order
                        paginator.add_line(f'* размещено ордеров: {len(oo)}')
                        paginator.add_line(f'* осталось {'закупить' if is_buy_order else 'продать'}: {remain:,d} шт')
                        paginator.add_line(f'* {'ордера исполнены' if is_multi_order else 'ордер исполнен'} на:'
                                           f' {100.0*(1.0-remain/total):,.1f}%')
                        if not is_multi_order:
                            issuer: str = oo[0].issuer.character_name if oo[0].issuer else str(oo[0].issuer_id)
                            paginator.add_line(f'* ордер выставлен по цене: `{oo[0].price:,.2f}` ISK (`{issuer}`)')
                        else:
                            paginator.add_line('* ордера выставлены по ценам:')
                            for o in oo:
                                issuer: str = o.issuer.character_name if o.issuer else str(o.issuer_id)
                                paginator.add_line(f'  {o.volume_remain:,d} шт по цене `{o.price:,.2f}` ISK '
                                                   f'(`{issuer}`), остаток {100.0*o.volume_remain/o.volume_total:,.1f}%')
                        paginator.add_line(f'* на общую сумму: `{sum([_.price * _.volume_remain for _ in oo]):,.2f}` ISK')
                        if is_buy_order:
                            paginator.add_line(f'* суммарный эскроу: `{sum([_.escrow for _ in oo if _.escrow]):,.2f}` ISK')
        if paginator:
            for page in paginator.pages:
                embeds = [_ for _ in [sell_embed, buy_embed] if _ is not None]
                if not embeds: embeds = None
                await ctx.send(page, embeds=embeds)
                sell_embed = None
                buy_embed = None
        elif item is None:
            await ctx.send(f'Предмет с названием `{product_name}` неизвестен')
        else:
            await ctx.send(f'Торговля предметом `{product_name}` не ведётся', embed=general_embed)
        del database

    @commands.command(
        pass_context=True,
        description='Получить сведения о производстве/модернизации предмета (следует использовать кавычки для названий '
                    'с пробелами-разделителями).\nНапример:\nQ.jobs Paladin\nQ.jobs "Fernite Carbide"',
        help="Получить сведения о производстве/модернизации предмета")
    async def jobs(
            self,
            ctx: commands.Context,
            product_name: str = commands.parameter(description='Название предмета')):
        database: Database = Database(
            all_known_type_ids=True,
            corporation_assets=True,  # TODO: здесь для загрузки названий контейнеров, хотя можно смотреть работы
            corporation_container_places=True,
            corporation_industry_jobs_active=True,
            conveyor_limits=True,  # используется для формирования полей embed объекта
            conveyor_requirements=True)  # используется для формирования полей embed объекта
        paginator: typing.Optional[discord.ext.commands.Paginator] = None
        embed: typing.Optional[discord.Embed] = None
        product_name = self.strip_eve_online_type_name(product_name)
        item: typing.Optional[db.QSwaggerTypeId] = self.get_type_id_by_type_name(database, product_name)
        if item:
            conveyor_limits: typing.Optional[typing.List[db.QSwaggerConveyorLimit]] = \
                database.qid.get_conveyor_limits(item.type_id)
            conveyor_requirement: typing.Optional[db.QSwaggerConveyorRequirement] = \
                database.qid.get_conveyor_requirement(item.type_id)
            # ---
            embed = discord.Embed(title=item.name, description=self.get_item_description(item), colour=0x337AB7)
            embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
            if not conveyor_limits:
                embed.add_field(name='Порог производства', value='(не задан)', inline=False)
            else:
                embed.add_field(name='Порог производства',
                                value=f'{sum([_.approximate for _ in conveyor_limits]):,d}',
                                inline=False)
            if conveyor_requirement:
                embed.add_field(name='Выставлено на продажу',
                                value=f'{conveyor_requirement.trade_remain:,d}',
                                inline=True)
            embed.add_field(name='Подготовлено чертежей', value='?', inline=True)
            # ---
            calculated_quantity: int = 0
            for corporation_id, corporation in database.qid.corporations.items():
                calculated: typing.Dict[typing.Optional[int], typing.List[db.QSwaggerCorporationIndustryJob]] = {}
                for j in corporation.industry_jobs_active.values():
                    if j.product_type_id == item.type_id:
                        calculated_quantity += j.runs
                        l: typing.List[db.QSwaggerCorporationIndustryJob] = calculated.get(j.output_location_id)
                        if l:
                            l.append(j)
                        else:
                            calculated[j.output_location_id] = [j]
                if not calculated:
                    continue
                if not paginator:
                    paginator = discord.ext.commands.Paginator(prefix='', suffix='')
                    paginator.add_line(f'`{item.name}`')
                for output_location_id, jobs in calculated.items():
                    installer_ids: typing.Set[int] = set([_.installer_id for _ in jobs])
                    output_name: str = '(неизвестно)'
                    if output_location_id is not None:
                        l: typing.Optional[db.QSwaggerCorporationAssetsItem] = jobs[0].output_location
                        if l and l.name:
                            output_name = l.name
                        else:
                            output_name = str(output_location_id)
                    paginator.add_line(f'Работы с выходом в `{output_name}`:')
                    line_prefix: str = '* '
                    if len(installer_ids) > 1:
                        paginator.add_line(f'{line_prefix}выполняется {sum([_.runs for _ in jobs])} прогонов в {len(jobs)} работах')
                        line_prefix = '  ' + line_prefix
                    for installer_id in installer_ids:
                        jj: typing.List[db.QSwaggerCorporationIndustryJob] = \
                            [_ for _ in jobs if _.installer_id == installer_id]
                        if jj[0].installer:
                            installer: str = jj[0].installer.character_name
                        else:
                            installer: str = str(installer_id)
                        paginator.add_line(f'{line_prefix}`{installer}` запустил {sum([_.runs for _ in jj])} прогонов'
                                           f' в {len(jj)} работах')
            embed.add_field(name='Производится', value=f'{calculated_quantity:,d} прогона', inline=True)
        if paginator:
            for page in paginator.pages:
                await ctx.send(page, embed=embed)
                embed = None
        elif item is None:
            await ctx.send(f'Предмет с названием `{product_name}` неизвестен')
        else:
            await ctx.send(f'Производство/модернизация `{product_name}` не ведётся', embed=embed)
        del database

    @commands.command(
        pass_context=True,
        description='Получить расчёт стоимости производства, найти профит от продажи (следует использовать кавычки для '
                    'названий с пробелами-разделителями).\nНапример:\nQ.industry Purifier\nQ.industry "Ogre II"',
        help="Получить расчёт стоимости производства, найти профит от продажи")
    async def industry(
            self,
            ctx: commands.Context,
            product_name: str = commands.parameter(description='Название предмета'),
            details: typing.Literal['full', 'lite'] = commands.parameter(description='Уровень детализации full/lite',
                                                                         default='lite')):
        database: Database = Database(
            all_known_type_ids=True,
            blueprints=True,
            conveyor_formulas=True,
            stations=True)
        paginator: typing.Optional[discord.ext.commands.Paginator] = None
        embed: typing.Optional[discord.Embed] = None
        product_name = self.strip_eve_online_type_name(product_name)
        item: typing.Optional[db.QSwaggerTypeId] = self.get_type_id_by_type_name(database, product_name)
        if item:
            fake_jita_sell_orders: bool = item.group_id in [
                30,  # Titan
                659,  # Supercarrier
                1538,  # Force Auxiliary
                547,  # Carrier
                4594,  # Lancer Dreadnought
                485,  # Dreadnought
            ]
            # ---
            embed = discord.Embed(title=item.name, description=self.get_item_description(item), colour=0x337AB7)
            embed.set_image(url=f"https://imageserver.eveonline.com/Type/{item.type_id}_64.png")
            # ---
            conveyor_formulas: typing.Optional[typing.List[db.QSwaggerConveyorFormula]] = \
                database.qid.get_conveyor_formulas(item.type_id)
            if conveyor_formulas:
                conveyor_formulas = [_ for _ in conveyor_formulas if _.trade_hub_id == 60003760]
            if conveyor_formulas:
                f0: db.QSwaggerConveyorFormula = conveyor_formulas[0]
                products_per_single_run: int = f0.products_per_single_run
                # сортируем либо по уменьшению профита (если известны цены на продажу)
                # либо сортируем по возрастанию стоимости постройки
                if not fake_jita_sell_orders and f0.single_product_profit:
                    conveyor_formulas.sort(key=lambda x: x.single_product_profit, reverse=True)
                else:
                    conveyor_formulas.sort(key=lambda x: x.single_product_cost, reverse=False)
                # ---
                paginator = discord.ext.commands.Paginator(prefix='', suffix='')
                paginator.add_line(f'`{item.name}`')
                # ---
                if not fake_jita_sell_orders:
                    if not f0.products_recommended_price:
                        paginator.add_line('Рекомендованная цена 1 шт продукта: (нет данных о ценах)')
                    else:
                        paginator.add_line(
                            '```fix\n'
                            f'Рекомендованная цена 1 шт продукта {f0.products_recommended_price/f0.products_num:,.2f} ISK\n'
                            '```')
                        embed.add_field(
                            name='Рекомендованная цена в Jita',
                            value=f'{f0.products_recommended_price/f0.products_num:,.2f} ISK',
                            inline=False)
                # ---
                if not f0.prior_blueprint_type_id:
                    if f0.blueprint:
                        paginator.add_line(f'Чертёж: {f0.blueprint.blueprint_type.name} (`{f0.blueprint_type_id}`)')
                    else:
                        paginator.add_line(f'Чертёж: № `{f0.blueprint_type_id}`')
                else:
                    paginator.add_line('Чертежи:')
                    for blueprint, blueprint_type_id in [(f0.blueprint, f0.blueprint_type_id),
                                                         (f0.prior_blueprint, f0.prior_blueprint_type_id)]:
                        if blueprint:
                            paginator.add_line(f'  {blueprint.blueprint_type.name} (`{blueprint_type_id}`)')
                        else:
                            paginator.add_line(f'  чертёж № `{blueprint_type_id}`')
                if details == 'full':
                    paginator.add_line(f'Код производства: `{f0.activity_id}`')
                paginator.add_line(f'Кол-во продукции за 1 прогон: `{products_per_single_run:,d}`')
                paginator.add_line(f'Комиссия при закупке сырья: `{f0.buying_brokers_fee*100.0:,.2f}` %')
                if not fake_jita_sell_orders:
                    paginator.add_line(f'Комиссия и налог с продаж: `{f0.sales_brokers_fee*100.0:,.2f} +'
                                       f' {f0.sales_tax:,.2f} = {100.0*(f0.sales_brokers_fee+f0.sales_tax):,.2f}` %')
                paginator.add_line(f'Цена топляка для Rhea: `{f0.fuel_price_isk:,.2f}` ISK')
                for f in conveyor_formulas:
                    value: str = ''
                    if not fake_jita_sell_orders and f.single_product_profit:
                        value += f'{'Убыток: ' if f.single_product_profit < 0.01 else 'Доход: '}' \
                                 f'{f.single_product_profit:,.2f} ISK\n'
                    value += f'Итого: {self.simplify_isk(f.single_product_cost)} ISK'
                    if fake_jita_sell_orders:
                        value += f'\nМатериалы: {self.simplify_isk(f.materials_cost)} ISK'
                        value += f'\nРаботы: {self.simplify_isk(f.jobs_cost)} ISK'
                    embed.add_field(
                        name=f'Без декриптора, ME={f.material_efficiency}'
                             if f.decryptor_type_id is None
                             else f.decryptor_type.name,
                        value=value,
                        inline=True)
                for f in conveyor_formulas:
                    if f.decryptor_type_id is None:
                        paginator.add_line(f'### Декриптор не используется, формула № `{f.formula_id}`')
                    else:
                        paginator.add_line(f'### Декриптор `{f.decryptor_type.name}` (`{f.decryptor_type_id}`),'
                                           f' формула № `{f.formula_id}`')
                    paginator.add_line(f'Нижний порог продажи 1 шт продукта `{f.product_mininum_price:,.2f}` ISK')
                    if not fake_jita_sell_orders:
                        if not f.single_product_profit:
                            paginator.add_line(f'Профит производства 1 шт продукта: (нет данных о ценах)')
                        else:
                            paginator.add_line(f"""```diff
{'-' if f.single_product_profit < 0.01 else '+'} Профит производства 1 шт продукта {f.single_product_profit:,.2f} ISK ({100.0*f.single_product_profit/f.total_gross_cost:,.2f} %)
```""")
                    piece_desc_short: str = '1 шт' if f.products_num == 1 else 'партии'
                    piece_desc_long: str = '1 шт продукта' if f.products_num == 1 else 'партии продукции'
                    paginator.add_line(f'Прогоны `{f.customized_runs}` шт')
                    paginator.add_line(f'Запуск работ `{f.jobs_cost:,.2f}` ISK')
                    paginator.add_line(f'* Партия продукции `{f.customized_runs} * {f.products_per_single_run} ='
                                       f' {f.products_num}` шт')
                    paginator.add_line(f'  Стоимость материалов `{f.materials_cost:,.2f}` ISK')
                    paginator.add_line(f'  Закуп материалов в Jita `{f.materials_cost_with_fee:,.2f}` ISK')
                    paginator.add_line(f'  Объём материалов `{f.purchase_volume:,.2f}` m³')
                    paginator.add_line(f'  Доставка материалов `{f.materials_transfer_cost:,.2f}` ISK')
                    paginator.add_line(f'* Объём {piece_desc_long} `{f.ready_volume:,.2f}` m³')
                    if f.ready_transfer_cost < 0.001:
                        paginator.add_line(f'  Вывоз {piece_desc_long}: (вывоз не запланирован)')
                    else:
                        paginator.add_line(f'  Вывоз {piece_desc_long} `{f.ready_transfer_cost:,.2f}` ISK')
                    if fake_jita_sell_orders or not f.products_recommended_price:
                        paginator.add_line(f'* Рекомендованная стоимость {piece_desc_short}: (нет данных о ценах)')
                    else:
                        paginator.add_line(f'* Рекомендованная стоимость {piece_desc_short} `{f.products_recommended_price:,.2f}` ISK')
                        paginator.add_line(f'  Комиссия с продаж {piece_desc_short} `{f.products_sell_fee_and_tax:,.2f}` ISK')
                        paginator.add_line(f'  Прибыль от продажи {piece_desc_short} `{f.single_product_price_wo_fee_tax:,.2f}` ISK')
                        if f.products_num > 1:
                            paginator.add_line(f'  Прибыль от продажи 1 шт продукта `{f.single_product_price_wo_fee_tax:,.2f}` ISK')
                    paginator.add_line(f'* Затраты на производство {piece_desc_short} `{f.total_gross_cost:,.2f}` ISK')
                    if f.products_num > 1:
                        paginator.add_line(f'  Затраты на производство 1 шт `{f.single_product_cost:,.2f}` ISK')
                    # прекращаем вывод сведений с другими вариантами производства этого продукта, если details не full
                    if details == 'lite':
                        break
        if paginator:
            for page in paginator.pages:
                await ctx.send(page, embed=embed)
                embed = None
        elif item is None:
            await ctx.send(f'Предмет с названием `{product_name}` не найден')
        else:
            await ctx.send(f'Нет рассчитанной формулы производства `{product_name}` (обратитесь к разработчику)',
                           embed=embed)
        del database


@bot.event
async def on_ready():
    await bot.add_cog(StatusCommands())
    await bot.add_cog(InformationCommands())


def main():
    if not argv_prms["corporation"]:
        console_app.print_version_screen()
        console_app.print_help_screen(0)
        return
    bot.run(q_discord_settings.g_token)


if __name__ == "__main__":
    main()
