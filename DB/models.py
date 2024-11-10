from datetime import datetime

import sqlalchemy as db
from sqlalchemy import Table

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from DB.enums import Belong

Base = declarative_base()


def getData(dt: datetime = None) -> str:
    if not dt:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


UserDepartament: Table = db.Table('u_x_d', Base.metadata,
                                  db.Column('department_id', db.Integer,
                                            db.ForeignKey('public.department.department_id'),
                                            primary_key=True),
                                  db.Column('user_id', db.Integer, db.ForeignKey('public.users.user_id'),
                                            primary_key=True),
                                  schema='public')

FranchiseEmployees = db.Table('f_x_p', Base.metadata,
                              db.Column('franchise_id',
                                        db.Integer,
                                        db.ForeignKey('business_entity.franchise.franchise_id'),
                                        primary_key=True),
                              db.Column('participant_id',
                                        db.Integer,
                                        db.ForeignKey('public.users.user_id'),
                                        primary_key=True),
                              schema='public')


class Franchise(Base, SerializerMixin):
    """
    Франчайзи
    """

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __table_args__ = {'schema': 'business_entity'}
    __tablename__ = 'franchise'

    franchise_id = db.Column(db.Integer, primary_key=True, nullable=True)
    franchise_name = db.Column(db.String(64))
    inn = db.Column(db.String())
    name = db.Column(db.String())
    kpp = db.Column(db.String())
    first_name = db.Column(db.String())
    middle_name = db.Column(db.String())
    phone = db.Column(db.String(20))
    last_name = db.Column(db.String())
    birth_date = db.Column(db.String())
    birth_place = db.Column(db.String())
    passport_series = db.Column(db.String())
    passport_number = db.Column(db.String())
    passport_date = db.Column(db.Date)
    registration_address = db.Column(db.String())
    resident = db.Column(db.String())
    document_url = db.Column(db.String())
    document_id = db.Column(db.String())
    account = db.Column(db.String())
    bank_code = db.Column(db.String())
    beneficiary_id = db.Column(db.String())
    virtual_account_id = db.Column(db.String())
    status = db.Column(db.String(8), default='inactive')
    belong = db.Column(db.String(32))
    city_code = db.Column(db.String(16))
    ogrnip = db.Column(db.String(32))
    legal_status = db.Column(db.String(2))
    is_active = db.Column(db.Boolean)
    franchise_type = db.Column(db.String(64))
    employees = relationship('User', secondary=FranchiseEmployees, back_populates='franchise', lazy='joined')
    agreements = relationship('FranchiseBroker', foreign_keys='FranchiseBroker.franchise_id', lazy='joined')
    street = db.Column(db.String)
    home_number = db.Column(db.String)
    room_type = db.Column(db.String)
    flat = db.Column(db.String)
    bank_name = db.Column(db.String)
    corresp_acc = db.Column(db.String)
    @property
    def fio(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'


class Report(Base):
    """
    акты по смете
    """
    __tablename__ = 'certificates'
    __table_args__ = {'schema': 'business_entity'}

    certificate_code = db.Column(db.String(32), primary_key=True)
    budgets_id = db.Column(db.Integer, primary_key=True)
    certificate_num = db.Column(db.Integer)
    create_date = db.Column(db.DateTime, default=getData)
    amount = db.Column(db.Float)
    signing_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)
    signing_version = db.Column(db.Integer)
    is_splited = db.Column(db.Boolean)


class ObjectBudget(Base):
    """
    Справочник связи между объектом-сметой и клиентом
    """
    __tablename__ = 'object_x_budget'
    __table_args__ = {'schema': 'relation'}

    object_id = db.Column(db.Integer, primary_key=True)
    budgets_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('business_entity.clients.client_id'))
    created_by = db.Column(db.Integer, primary_key=True)


class ObjectFranchise(Base):
    """
    Связь объекта и франчайзи
    """
    __table_args__ = {'schema': 'relation'}
    __tablename__ = 'objects_x_franchise'

    object_id = db.Column(db.Integer, primary_key=True)
    franchise_id = db.Column(db.Integer, primary_key=True, nullable=True)
    start_date = db.Column(db.DateTime, default=getData)
    end_date = db.Column(db.DateTime, default=getData(datetime.max))


class Department(Base):
    """
    Департамент
    """
    __tablename__ = 'department'
    __table_args__ = {'schema': 'public'}

    department_id = db.Column(db.Integer, primary_key=True, nullable=False)
    department_name = db.Column(db.String(128))
    department_code = db.Column(db.String(64))
    rus_code = db.Column(db.String(16))
    users = relationship('User', secondary=UserDepartament, back_populates='department', single_parent=True,
                         lazy=False)


class User(Base, SerializerMixin):
    """
    сокращённый ORM для пользователя
    """
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    serialize_only = ('user_id', 'first_name', 'second_name', 'middle_name', 'phone', 'email', 'alias', 'photo_url')

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(32))
    second_name = db.Column(db.String(32))
    middle_name = db.Column(db.String(32))
    email = db.Column(db.String(100), nullable=False)
    hashPassword = db.Column(db.String(300))
    confirmed_flag = db.Column(db.Boolean, server_default='0')
    authenticated_flag = db.Column(db.Boolean, server_default='0')
    phone = db.Column(db.String(20))
    amocrm_id = db.Column(db.Integer)
    telegram_id = db.Column(db.Integer)
    alias = db.Column(db.String(10))
    photo_url = db.Column(db.String(256))
    department = relationship('Department', secondary=UserDepartament, back_populates='users', lazy=False)
    franchise = relationship('Franchise', secondary=FranchiseEmployees, back_populates='employees', lazy=False)


class Deals(Base):
    """
    Таблица логирования сделок
    """
    __tablename__ = 'deals'
    __table_args__ = {'schema': 'log'}

    deal_id = db.Column(db.String(), nullable=False)
    beneficiary_id = db.Column(db.String(), nullable=False)
    document_id = db.Column(db.String())
    success_added = db.Column(db.Boolean, nullable=False, default=False)
    deal_status = db.Column(db.String(), nullable=False, default='new')
    certificate_code = db.Column(db.String(32), primary_key=True)
    created_date = db.Column(db.TIMESTAMP, nullable=False, default=getData)
    updated_date = db.Column(db.TIMESTAMP, nullable=False, default=getData)


class ReportAcquiring(Base):
    """
    Таблица для отчётов эквайринга
    """
    __tablename__ = 'acquiring_reports'
    __table_args__ = {'schema': 'business_entity'}
    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)
    add_date = db.Column(db.TIMESTAMP, default=getData)
    url = db.Column(db.String(512))
    name = db.Column(db.String(512))
    received = db.Column(db.TIMESTAMP)
    report_id = db.Column(db.String(64))


class TransactionReport(Base):
    """
    Таблица для платёжных транзакций
    """
    __tablename__ = 'transaction_report'
    __table_args__ = {'schema': 'business_entity'}

    report_id = db.Column(db.String(64), primary_key=True)
    report_date = db.Column(db.TIMESTAMP)
    transaction_id = db.Column(db.String(64), primary_key=True)
    transaction_date = db.Column(db.TIMESTAMP)
    payment_number = db.Column(db.String(32))
    payment_date = db.Column(db.TIMESTAMP)
    amount = db.Column(db.Float)
    fee = db.Column(db.Float)
    total_amount = db.Column(db.Float)


class Transactions(Base, SerializerMixin):
    """
    Таблица для платёжных транзакций
    """
    serialize_rules = ('-document_id', '-acquiring_order_id')

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction'
    __table_args__ = {'schema': 'business_entity'}

    transaction_id = db.Column(db.String(64), nullable=False, primary_key=True)
    payment_type = db.Column(db.String(64))
    transaction_type_code = db.Column(db.String(64), db.ForeignKey('dimension.transaction_type.transaction_type_code'))
    created_date = db.Column(db.TIMESTAMP, default=getData)
    created_by = db.Column(db.Integer)
    object_id = db.Column(db.Integer, db.ForeignKey('business_entity.estimate_objects.object_id'))
    transaction_date = db.Column(db.TIMESTAMP)
    assets_liabilities = db.Column(db.Boolean, default=False)  # Для заполнения при создании trs
    cash = db.Column(db.Boolean, default=False)  # Для заполнения при создании trs
    amount = db.Column(db.Float)
    is_approved = db.Column(db.Boolean)
    approved_date = db.Column(db.TIMESTAMP)
    approved_by = db.Column(db.Integer)
    prepayment_flag = db.Column(db.Boolean, default=True)  # Для заполнения при создании trs
    entity_type = db.Column(db.String(64))
    entity_code = db.Column(db.String(64))
    acquiring_order_id = db.Column(db.String(64))
    deal_id = db.Column(db.String(64))
    document_id = db.Column(db.String(64))
    is_closed = db.Column(db.Boolean)
    is_identify = db.Column(db.Boolean)
    is_assigned = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    order_url = db.Column(db.String(1024))
    fee = db.Column(db.Float)
    qr_code = db.Column(db.String)
    receipt = db.Column(db.String)
    comment = db.Column(db.String(512))
    franchise_id = db.Column(db.Integer)
    # связи
    type = relationship('TransactionTypes', lazy='joined')
    statuses = relationship('TransactionStatus', lazy='joined')
    object = relationship('EstimateObjects', lazy='joined')


class TransactionStatus(Base, SerializerMixin):
    """
    Таблица для статусов платёжных транзакций
    """
    serialize_rules = ('-transaction_id',)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction_status'
    __table_args__ = {'schema': 'business_entity'}

    transaction_id = db.Column(db.String(), db.ForeignKey('business_entity.transaction.transaction_id'),
                               primary_key=True)
    start_date = db.Column(db.TIMESTAMP, default=getData, primary_key=True)
    end_date = db.Column(db.TIMESTAMP, default=getData(datetime.max))
    status_code = db.Column(db.String(64), db.ForeignKey('dimension.transaction_status.status_code'), primary_key=True)
    status = relationship('TransactionStatusDimensions', lazy='joined')


class TransactionStatusDimensions(Base, SerializerMixin):
    """
    Таблица для статусов платёжных транзакций
    """
    serialize_rules = ('-status_code',)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction_status'
    __table_args__ = {'schema': 'dimension'}

    status_code = db.Column(db.String(64), primary_key=True)
    description = db.Column(db.String(256))


class TransactionTypes(Base, SerializerMixin):
    """
    Таблица для типов платёжных транзакций
    """
    serialize_rules = ('-transaction_type_code',)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction_type'
    __table_args__ = {'schema': 'dimension'}

    transaction_type_code = db.Column(db.String(64), primary_key=True)
    description = db.Column(db.String(512))
    transaction_category = db.Column(db.String(64))
    unit_code = db.Column(db.String(8), db.ForeignKey('public.unit.unit_code'))
    # связи
    unit = relationship('Units', lazy='joined')


class Units(Base, SerializerMixin):
    """
    Таблица для типов платёжных транзакций
    """
    serialize_rules = ('-unit_code',)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'unit'
    __table_args__ = {'schema': 'public'}

    unit_code = db.Column(db.String(8), primary_key=True)
    unit_name = db.Column(db.String(64))


class EstimateObjects(Base, SerializerMixin):
    """
    Таблица объектов с данными смет (укороченное)
    """
    serialize_rules = ('-object_id',)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'estimate_objects'
    __table_args__ = {'schema': 'business_entity'}

    object_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    address = db.Column(db.String(256))
    is_nominal = db.Column(db.Boolean)
    cash_object = db.Column(db.Boolean, default=False)


class AmoObjects(Base, SerializerMixin):
    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __table_args__ = {'schema': 'business_entity'}
    __tablename__ = 'amocrm_objects'

    objects_id = db.Column(db.Integer, primary_key=True)
    phase_id = db.Column(db.Integer)
    franchise_id = db.Column(db.Integer)


class CertificateDocs(Base):
    """
    документы акта
    """
    __tablename__ = 'documents_info'
    __table_args__ = {'schema': 'business_entity'}

    documentation_id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.String(32), primary_key=True)
    entity_type = db.Column(db.String(32), default='certificate')
    date_add = db.Column(db.DateTime, default=getData())
    documentation_name = db.Column(db.String(1024))
    documentation_url = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean)

class ParticipantsXObject(Base):
    __tablename__ = 'participants_x_object'
    __table_args__ = {'schema': 'relation'}

    object_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('public.users.user_id'))
    department_id = db.Column(db.Integer, db.ForeignKey('public.department.department_id'))
    date_start = db.Column(db.TIMESTAMP)
    date_end = db.Column(db.TIMESTAMP)


class ActsActivity(Base):
    __tablename__ = 'acts_activity'
    __table_args__ = {'schema': 'business_entity'}

    certificate_code = db.Column(db.String(32), primary_key=True)
    certificate_status = db.Column(db.String(16))
    certificate_status_code = db.Column(db.String(16))
    date_start = db.Column(db.TIMESTAMP, primary_key=True)
    date_end = db.Column(db.TIMESTAMP, default=getData(datetime.max))
    comment = db.Column(db.String(1024))


class Transaction(Base, SerializerMixin):

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction'
    __table_args__ = {'schema': 'report'}

    franchise_id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.String(), primary_key=True)
    amount = db.Column(db.Float)
    amount_sdd = db.Column(db.Float)
    ssd_date = db.Column(db.TIMESTAMP)
    amount_dm = db.Column(db.Float)
    dm_date = db.Column(db.TIMESTAMP)
    amount_franchise = db.Column(db.Float)
    franchise_date = db.Column(db.TIMESTAMP)
    deal_date = db.Column(db.TIMESTAMP)


class TransactionManual(Base, SerializerMixin):

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'transaction'
    __table_args__ = {'schema': 'dimension'}

    franchise_id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.String(), primary_key=True)
    amount = db.Column(db.Float)
    amount_sdd = db.Column(db.Float)
    ssd_date = db.Column(db.TIMESTAMP)
    amount_dm = db.Column(db.Float)
    dm_date = db.Column(db.TIMESTAMP)
    amount_franchise = db.Column(db.Float)
    franchise_date = db.Column(db.TIMESTAMP)
    deal_date = db.Column(db.TIMESTAMP)


class CertificateStatus(Base):
    """
    статусы актов
    """
    __tablename__ = 'certificate_status'
    __table_args__ = {'schema': 'business_entity'}

    certificate_code = db.Column(db.String(32), primary_key=True)
    status_id = db.Column(db.Integer, primary_key=True)
    date_start = db.Column(db.DateTime, primary_key=True)
    date_end = db.Column(db.DateTime, default=getData(datetime.max))
    user_id = db.Column(db.Integer)


class CertificateVersion(Base):
    """
    версии актов
    """
    __tablename__ = 'certificates_x_version'
    __table_args__ = {'schema': 'relation'}

    certificate_code = db.Column(db.String(32), db.ForeignKey('business_entity.certificates.certificate_code'),
                                 primary_key=True)
    version_num = db.Column(db.Integer, primary_key=True)
    version_name = db.Column(db.String(128))
    create_date = db.Column(db.DateTime, default=getData())
    amount = db.Column(db.Float)
    created_by = db.Column(db.Integer)
    updated_date = db.Column(db.DateTime, default=getData())
    updated_by = db.Column(db.Integer)


class GeneratorOrder(Base):
    __tablename__ = 'order'
    __table_args__ = {'schema': 'generator_id'}
    order_id = db.Column(
        db.String(32),
        primary_key=True,
        nullable=False,
        server_default="'П-'::text || nextval('generator_id.order_id_seq'::regclass"
    )


class Credits(Base):
    __tablename__ = 'credits'
    __table_args__ = {'schema': 'business_entity'}

    credit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    object_id = db.Column(db.Integer)
    created_date = db.Column(db.TIMESTAMP, default=getData)
    contract_type = db.Column(db.String())
    initial_amount = db.Column(db.Float)
    amount = db.Column(db.Float)
    status = db.Column(db.String(), default='На одобрении')
    merchant_id = db.Column(db.Integer)
    creditor_id = db.Column(db.Integer)
    program = db.Column(db.Integer, db.ForeignKey('dimension.credit_program.credit_program_id'))


class CreditProgram(Base):
    __tablename__ = 'credit_program'
    __table_args__ = {'schema': 'dimension'}

    credit_program_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    loan_term = db.Column(db.Integer)
    discount = db.Column(db.Float)
    rate = db.Column(db.Float)
    creditor_id = db.Column(db.Integer)


class BrokerFee(Base):
    __tablename__ = 'brokers_fee'
    __table_args__ = {'schema': 'dimension'}

    program_id = db.Column(db.Integer, primary_key=True)
    fee = db.Column(db.Float)
    broker_id = db.Column(db.Integer, primary_key=True)
    broker_type = db.Column(db.String)


class BrokerProgram(Base):
    __tablename__ = 'brokers_program'
    __table_args__ = {'schema': 'dimension'}

    program_id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String)
    franchise_type = db.Column(db.String)


class FranchiseBroker(Base, SerializerMixin):

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    serialize_rules = ("-broker", "broker_name")

    __tablename__ = 'franchise_x_brokers'
    __table_args__ = {'schema': 'relation'}

    franchise_id = db.Column(db.Integer, db.ForeignKey('business_entity.franchise.franchise_id'), primary_key=True)
    broker_id = db.Column(db.Integer, db.ForeignKey('business_entity.franchise.franchise_id'), primary_key=True)
    document_num = db.Column(db.String)
    document_date = db.Column(db.Date)
    documentation_id = db.Column(db.String, db.ForeignKey('business_entity.documents_info.documentation_id'))
    broker = relationship('Franchise', primaryjoin="Franchise.franchise_id == FranchiseBroker.broker_id", lazy='joined')

    @property
    def broker_name(self):
        return self.broker.name


class Order(Base, SerializerMixin):
    serialize_rules = ('-items.order_id', '-items.item_detail.item_id')

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'orders'
    __table_args__ = {'schema': 'transaction'}

    order_id = db.Column(db.VARCHAR, primary_key=True, nullable=False,
                         server_default="'OR'::text || nextval('transaction.get_order_num'::regclass", )
    external_id = db.Column(db.VARCHAR)
    contract_date = db.Column(db.Date)


class Tranche(Base):
    __tablename__ = 'tranche'
    __table_args__ = {'schema': 'business_entity'}
    tranche_id = db.Column(db.String, primary_key=True,
                           server_default="'TR'::text || nextval('business_entity.get_tranche_id_num'::regclass)")
    order_id = db.Column(db.String)


class FranchiseOld(Base):
    """
    Бэкап базы франчайзи
    """

    __tablename__ = 'franchise_old'
    __table_args__ = {'schema': 'business_entity'}

    franchise_id = db.Column(db.Integer, primary_key=True, nullable=True)
    virtual_account_id = db.Column(db.String())
    belong = db.Column(db.String(32), default=Belong.EXTERNAL.value)
    beneficiary_id = db.Column(db.String())


class TransferTransactions(Base):
    """
    Табоица перевода денег между ВС разных НС
    """

    __tablename__ = 'transfer'
    __table_args__ = {'schema': 'transaction'}

    id = db.Column(db.String(128), primary_key=True, nullable=False)
    amount = db.Column(db.Float)
    franchise_id = db.Column(db.Integer)
    type = db.Column(db.String, default='transfer')
    transaction_id = db.Column(db.Integer)
    is_success = db.Column(db.Boolean, default=False)


class EntityActivity(Base):
    __tablename__ = 'activity'
    __table_args__ = {'schema': 'business_entity'}

    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_id = db.Column(db.String(128), nullable=False)
    entity_type = db.Column(db.String(64))
    comment = db.Column(db.String(1024))
    date_start = db.Column(db.DateTime, default=getData)
    date_end = db.Column(db.DateTime, default=getData(datetime.max))
    user_id = db.Column(db.Integer)
    department_id = db.Column(db.Integer)
    object_id = db.Column(db.Integer)


class UserXStatus(Base, SerializerMixin):

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

    __tablename__ = 'user_x_status'
    __table_args__ = {'schema': 'public'}

    user_id = db.Column(db.Integer, primary_key=True)
    user_status_id = db.Column(db.Integer)
    date_start = db.Column(db.TIMESTAMP, default=getData)
    date_end = db.Column(db.TIMESTAMP, default=getData(datetime.max))


class Waybill(Base):
    __tablename__ = 'waybill'
    __table_args__ = {'schema': 'business_entity'}

    waybill_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    waybill_num = db.Column(db.String())
    comment = db.Column(db.String())
    object_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    created_date = db.Column(db.TIMESTAMP)
    payment_date = db.Column(db.TIMESTAMP)
    waybill_type = db.Column(db.String(64))


class Refunds(Base):
    __tablename__ = 'refunds'
    __table_args__ = {'schema': 'finance'}

    refunds_id = db.Column(db.String,
                           primary_key=True,
                           server_default="'RF'::text || nextval('finance.get_refunds_num'::regclass")
    bik = db.Column(db.String)
    account = db.Column(db.String)
    status_id = db.Column(db.Integer)
    object_id = db.Column(db.Integer)
    created_by = db.Column(db.Integer)
    amount = db.Column(db.Float)
    type = db.Column(db.String(16))
    transaction_id = db.Column(db.String(64))
    create_date = db.Column(db.TIMESTAMP)
    execution_date = db.Column(db.TIMESTAMP)
    franchise_id = db.Column(db.Integer)


class Return(Base):
    __tablename__ = 'return'
    __table_args__ = {'schema': 'business_entity'}

    return_id = db.Column(db.String,
                          primary_key=True,
                          server_default="('RN'::text || nextval('business_entity.get_return_num'::regclass))")
    waybill_id = db.Column(db.Integer(), db.ForeignKey('business_entity.waybill.waybill_id'))
    amount = db.Column(db.Float)
    return_date = db.Column(db.TIMESTAMP)
    comment = db.Column(db.String())
    delivery_type = db.Column(db.Integer)
    returns_reason = db.Column(db.Integer)
    delivery_amount = db.Column(db.Float)
    weight = db.Column(db.Float)
    volume = db.Column(db.Float)
    place_count = db.Column(db.Integer)
    size = db.Column(db.Float)
    ready_date = db.Column(db.TIMESTAMP)
    pickup_date = db.Column(db.TIMESTAMP)
    delivery_date = db.Column(db.TIMESTAMP)
    acceptance_date = db.Column(db.TIMESTAMP)
    placement_date = db.Column(db.TIMESTAMP)
    created_by = db.Column(db.Integer)
    delivery_paid = db.Column(db.Boolean)
    transaction_id = db.Column(db.String())


class ControlEntityStatus(Base):
    __tablename__ = 'control_entity_x_status'
    __table_args__ = {'schema': 'relation'}

    control_entity_id = db.Column(db.String(), primary_key=True)
    control_status = db.Column(db.Integer, primary_key=True)
    date_start = db.Column(db.TIMESTAMP, default=getData)
    date_end = db.Column(db.TIMESTAMP, default=getData(datetime.max), primary_key=True)


class FranchiseXStatus(Base):
    __tablename__ = 'franchise_x_status'
    __table_args__ = {'schema': 'public'}
    franchise_id = db.Column(db.Integer, db.ForeignKey('business_entity.franchise.franchise_id'), primary_key=True)
    status_id = db.Column(db.Integer)
    date_start = db.Column(db.Date, default=getData)
    date_end = db.Column(db.Date, default=getData(datetime.max))


class Budgets(Base):
    """
    Таблица со списком смет
    """

    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'business_entity'}

    budgets_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    last_paid_cert = db.Column(db.Integer)
    contract_date = db.Column(db.DateTime)
    program_id = db.Column(db.Integer, db.ForeignKey('dimension.brokers_program.program_id'))


class Clients(Base):
    __tablename__ = 'clients'
    __table_args__ = {'schema': 'business_entity'}

    client_id = db.Column(db.Integer, primary_key=True, nullable=False)
    second_name = db.Column(db.String(64))
    first_name = db.Column(db.String(64))
    middle_name = db.Column(db.String(64))
    legal_status = db.Column(db.String(64))


class Object_x_Client(Base):
    """
    статусы актов во времени
    """
    __tablename__ = 'object_x_client'
    __table_args__ = {'schema': 'relation'}

    object_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, primary_key=True)


class Batch(Base):
    """
    Идентификаторы блоков загрузки
    """
    __tablename__ = 'batch'
    __table_args__ = {'schema': 'log'}

    batch_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_start = db.Column(db.TIMESTAMP, default=getData)
    date_end = db.Column(db.TIMESTAMP)
    business_entity = db.Column(db.String())


class Orders(Base):
    """
    Заказы ЧМ из 1C
    """
    __tablename__ = 'orders'
    __table_args__ = {'schema': 'shop_prorabam'}

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('log.batch.batch_id'))
    order_code = db.Column(db.String(32))
    amount = db.Column(db.Float)
    order_date = db.Column(db.Date)
    object_id = db.Column(db.Integer)
    foreman = db.Column(db.String(64))
    income_type = db.Column(db.String(32))
    internal_order_number = db.Column(db.String())
    parent_order = db.Column(db.String())


class OrderItem(Base):
    """
    Товар из корзины заказа ЧМ из 1C
    """
    __tablename__ = 'orders_items'
    __table_args__ = {'schema': 'shop_prorabam'}

    orders_items_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('log.batch.batch_id'))
    order_id = db.Column(db.String(32), db.ForeignKey('shop_prorabam.orders.order_id'))
    article = db.Column(db.Integer)
    amount = db.Column(db.Float)
    quantity = db.Column(db.Float)
    discount = db.Column(db.Float)
    discount_amount = db.Column(db.Float)
    unit = db.Column(db.String())


class SuperVisorXFranchisee(Base):
    __tablename__ = 's_x_f'
    __table_args__ = {'schema': 'public'}
    supervisor_id = db.Column(db.Integer, db.ForeignKey('public.users.user_id'), primary_key=True)
    franchise_id = db.Column(db.Integer, db.ForeignKey('public.users.user_id'), primary_key=True)
    date_start = db.Column(db.TIMESTAMP, primary_key=True, default=getData)
    date_end = db.Column(db.TIMESTAMP, primary_key=True, default=getData(datetime.max))


class SignSystemCreds(Base):
    """
    Учетные данные ФЗ в системах ЭЦП, в которых ФЗ зарегистрирован.
    """
    __tablename__ = 'sign_system_creds'
    __table_args__ = {'schema': 'digital_sign_systems'}

    sign_system_id = db.Column(db.Integer, primary_key=True)
    franchise_id = db.Column(db.Integer, primary_key=True)
    cred_name = db.Column(db.String(128), primary_key=True)
    cred_value = db.Column(db.String)


class SignSystem(Base):
    """
    Справочник систем ЭЦП.
    """
    __tablename__ = 'sign_systems'
    __table_args__ = {'schema': 'digital_sign_systems'}

    sign_system_id = db.Column(db.Integer, primary_key=True)
    sign_system_name = db.Column(db.String(128))
    sign_system_alias = db.Column(db.String(128))


class OrdersRaw(Base):
    """
    Сырой поток заказов ЧМ
    """
    __tablename__ = 'orders_raw'
    __table_args__ = {'schema': 'shop_prorabam'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('log.batch.batch_id'))
    json = db.Column(db.JSON)


class Product(Base):
    """
    Товары из 1С
    """

    __tablename__ = 'shop_prorabam'
    __table_args__ = {'schema': 'product'}

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.Integer)
    article = db.Column(db.String)
    section_name = db.Column(db.String(256))
    name = db.Column(db.String(512))
    unit = db.Column(db.String(128))
    description = db.Column(db.String(1024))
    src_product_code = db.Column(db.String(256))
    vendor_code = db.Column(db.String(64))
