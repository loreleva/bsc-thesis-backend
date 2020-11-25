CREATE TABLE IF NOT EXISTS errors.error(
	code errors.smallString NOT NULL,
	messagge errors.longString NOT NULL,
	PRIMARY KEY (code)
);

INSERT INTO errors.error values('VD001', 'Variable is composite, can not have a domain');
INSERT INTO errors.error values('VD002', 'Variable is simple, must have a domain');
INSERT INTO errors.error values('VD003', 'A category must have only one supercategory');
INSERT INTO errors.error values('VD004', 'Only composite variables can have a field');
INSERT INTO errors.error values('VD005', 'A composite field must contain variables of the same type');
INSERT INTO errors.error values('VD006', 'A composite variable must have at least one field');
INSERT INTO errors.error values('VD007', 'Incorrect value for the domain of the variable');
INSERT INTO errors.error values('VD008', 'Incorrect value for the range of the domain of the variable');
INSERT INTO errors.error values('VD009', 'Value is not in the enumerate domain of the variable');
INSERT INTO errors.error values('VD010', 'Only variables in the composite variable can have a value');
INSERT INTO errors.error values('VD011', 'Each mandatory field of the composite variable must have a value');
INSERT INTO errors.error values('VD012', 'Only the simple variable can have a value');
INSERT INTO errors.error values('VD013', 'An assignment must have at least a value');
INSERT INTO errors.error values('VD014', 'A composite variable can not have a value');
INSERT INTO errors.error values('VD015', 'Domain is not complete and disjoint');
INSERT INTO errors.error values('VD016', 'A composite variable can not contain itself');
INSERT INTO errors.error values('VD017', 'Incorrect attributes for the domain');
INSERT INTO errors.error values('VD018', 'The value is already assigned in the state, can not have a different value');
INSERT INTO errors.error values('VD019', 'A variable can be contained in a composite variable only one time');
INSERT INTO errors.error values('42703', 'Invalid data type for the attribute');
INSERT INTO errors.error values('23503', 'Foreign key violation');
INSERT INTO errors.error values('22008', 'Datetime overflow');
INSERT INTO errors.error values('23505', 'The key value already exists');

CREATE TABLE IF NOT EXISTS users.role(
	name users.smallString NOT NULL,
	PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS users.user(
	sub INTEGER NOT NULL,
	email users.longString NOT NULL,
	PRIMARY KEY(sub),
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS users.userrole(
	role users.smallString NOT NULL,
	sub INTEGER NOT NULL,
	PRIMARY KEY (role,sub),
	FOREIGN KEY (role) REFERENCES users.role(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (sub) REFERENCES users.user(sub) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.relcase(
	id INTEGER NOT NULL,
	stepsize_s public.intGZ NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.retrospectivecase(
	id INTEGER NOT NULL,
	description public.longString,
	start timestamp without time zone,
	sub INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES public.relcase(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (sub) REFERENCES users.user(sub) ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE SEQUENCE IF NOT EXISTS public.case_id
    AS INTEGER
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
    OWNED BY public.relcase.id;

ALTER TABLE ONLY public.relcase ALTER COLUMN id SET DEFAULT nextval('case_id');

CREATE TABLE IF NOT EXISTS public.state(
	relcase INTEGER NOT NULL,
	timestamp public.intGEZ NOT NULL,
	PRIMARY KEY (relcase, timestamp),
	FOREIGN KEY (relcase) REFERENCES public.relcase(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.category(
	name public.smallString NOT NULL,
	PRIMARY KEY(name)
);

INSERT INTO public.category values('VDRootCategory');

CREATE TABLE IF NOT EXISTS public.subcategory(
	super public.smallString NOT NULL,
	sub public.smallString NOT NULL,
	PRIMARY KEY (super,sub),
	FOREIGN KEY (super) REFERENCES public.category(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (sub) REFERENCES public.category(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.domain(
	name public.smallString NOT NULL,
	PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS public.variable(
	name public.smallString NOT NULL,
	type_fa public.var_type_fa NOT NULL,
	type_sc public.var_type_sc NOT NULL,
	category public.smallString NOT NULL,
	domain public.smallString,
	PRIMARY KEY (name),
	FOREIGN KEY (category) REFERENCES public.category(name) ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (domain) REFERENCES public.domain(name) ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.compositefield(
	owner public.smallString NOT NULL,
	field public.smallString NOT NULL,
	mandatory BOOLEAN NOT NULL,
	PRIMARY KEY (owner,field),
	FOREIGN KEY (owner) REFERENCES public.variable(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (field) REFERENCES public.variable(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.assignment(
	relcase INTEGER NOT NULL,
	timestamp public.intGEZ NOT NULL,
	ordernum public.intGZ NOT NULL,
	variable public.smallString NOT NULL,
	PRIMARY KEY (relcase,timestamp,ordernum),
	FOREIGN KEY (relcase,timestamp) REFERENCES public.state(relcase,timestamp) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (variable) REFERENCES public.variable(name) ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	UNIQUE (relcase,timestamp,variable)
);

CREATE TABLE IF NOT EXISTS public.SimpleVariableValue(
	relcase INTEGER NOT NULL,
	timestamp public.intGEZ NOT NULL,
	ordernum public.intGEZ NOT NULL,
	variable public.smallString NOT NULL,
	value public.real NOT NULL,
	PRIMARY KEY (relcase,timestamp,ordernum,variable),
	FOREIGN KEY (relcase,timestamp,ordernum) REFERENCES public.assignment(relcase,timestamp,ordernum) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY (variable) REFERENCES public.variable(name) ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.EnumerateDomain(
	domain public.smallString NOT NULL,
	PRIMARY KEY (domain),
	FOREIGN KEY (domain) REFERENCES public.domain(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS public.EnumerateValue(
	domain public.smallString NOT NULL,
	id public.intGZ NOT NULL,
	value public.smallString NOT NULL,
	PRIMARY KEY (domain,id),
	FOREIGN KEY (domain) REFERENCES public.EnumerateDomain(domain) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	UNIQUE (domain,value)
);

CREATE TABLE IF NOT EXISTS public.RangeDomain(
	domain public.smallString NOT NULL,
	min public.real NOT NULL,
	max public.real NOT NULL,
	step public.realGZ NOT NULL,
	type dom_type NOT NULL,
	PRIMARY KEY (domain),
	FOREIGN KEY (domain) REFERENCES public.domain(name) ON DELETE CASCADE ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
	UNIQUE (min,max,step,type)
);



