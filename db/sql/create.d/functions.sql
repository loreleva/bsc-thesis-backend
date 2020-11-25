CREATE OR REPLACE FUNCTION public.constraint_variable_domain() --check if a variable has a domain only if it is simple
	RETURNS TRIGGER
AS
$$
BEGIN
	IF (NEW.type_sc = 'composite' AND NEW.domain <> NULL) THEN
		RAISE EXCEPTION 'Variable % is composite, can not have a domain',NEW.name USING ERRCODE='VD001';

	ELSIF (NEW.type_sc = 'simple' AND NEW.domain = NULL) THEN
		RAISE EXCEPTION 'Variable % is simple, must have a domain',NEW.name USING ERRCODE='VD002';
	END IF;
	RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_variable_domain ON public.variable;
CREATE TRIGGER trigger_variable_domain BEFORE INSERT OR UPDATE OF type_sc,domain ON public.variable
FOR EACH ROW EXECUTE FUNCTION public.constraint_variable_domain();


------------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.constraint_category_unique_super() --check if a category has only one supercategory
	RETURNS TRIGGER
AS
$$
BEGIN
	IF (SELECT count(*) FROM public.subcategory sc WHERE sc.sub=NEW.sub) <> 1 THEN
		RAISE EXCEPTION 'A category must have only one supercategory' USING ERRCODE='VD003';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_category_unique_super ON public.subcategory;
CREATE CONSTRAINT TRIGGER trigger_category_unique_super AFTER INSERT OR UPDATE OF sub ON public.subcategory DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION public.constraint_category_unique_super();


------------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.category_tree(root smallstring) -- return the subcategories tree of a category
RETURNS table(
		super smallstring,
		sub smallstring
		)
AS
$$
BEGIN
	RETURN QUERY (WITH RECURSIVE tree AS (
		SELECT sc.super,sc.sub FROM public.subcategory sc WHERE sc.super=root
		UNION
		SELECT t.sub, subcat.sub FROM tree t, public.subcategory subcat WHERE t.sub=subcat.super
		) SELECT * FROM tree);
END;
$$
LANGUAGE 'plpgsql';


------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_composite_variable_type() --check if a composite variable has fields with the same type and if owner is a composite variable and if a field is not repeated in the tree
	RETURNS TRIGGER
AS
$$
DECLARE
	type record;
	category record;
	owner record;
BEGIN
	SELECT v.type_fa as type_owner, vv.type_fa as type_field, v.type_sc as type_sc_owner, vv.type_sc as type_sc_field INTO type FROM public.Variable v, public.Variable vv WHERE v.name=NEW.owner AND vv.name=NEW.field;
	IF (type.type_sc_owner = 'simple') THEN
		RAISE EXCEPTION 'Variable % is simple, can not have a field',NEW.owner USING ERRCODE='VD004';
	ELSIF (type.type_owner <> type.type_field) THEN 
		RAISE EXCEPTION 'Variables % and % are of different types',NEW.owner,NEW.field USING ERRCODE='VD005';
	ELSIF (NEW.owner = NEW.field) THEN
		RAISE EXCEPTION 'Composite % variable can not contain itself', category.field USING ERRCODE='VD017';
	END IF;
	FOR owner IN SELECT * FROM public.compositefield cf WHERE cf.field = NEW.field LOOP
		IF public.same_root(owner.owner, NEW.owner) OR public.tree_root(owner.owner, NEW.owner) OR public.tree_root(NEW.owner, owner.owner) THEN
			RAISE EXCEPTION 'A variable can be contained in a composite variable only one time' USING ERRCODE='VD020';
		END IF;
	END LOOP;
	RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_composite_variable_type ON public.compositefield;
CREATE TRIGGER trigger_composite_variable_type BEFORE INSERT ON public.compositefield
FOR EACH ROW EXECUTE FUNCTION public.constraint_composite_variable_type();


------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_composite_variable() -- check if a composite variable has fields after insert or update in variable
	RETURNS TRIGGER
AS
$$
BEGIN
	IF NOT EXISTS (SELECT * FROM public.compositefield c WHERE c.owner = NEW.name) THEN
		RAISE EXCEPTION 'Composite variable % must have at least one field',NEW.name USING ERRCODE='VD006';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_composite_variable ON public.variable;
CREATE CONSTRAINT TRIGGER trigger_composite_variable AFTER INSERT OR UPDATE OF type_sc ON public.variable DEFERRABLE INITIALLY DEFERRED 
FOR EACH ROW WHEN (NEW.type_sc = 'composite') EXECUTE FUNCTION public.constraint_composite_variable();

------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_composite_variable_compositefield_d() -- check if a composite variable has at least one field after a delete in compositefield
	RETURNS TRIGGER
AS
$$
DECLARE
	composite smallstring;
BEGIN
	IF EXISTS (SELECT * FROM public.variable v WHERE v.name=OLD.owner AND v.type_sc='composite') AND NOT EXISTS (SELECT * FROM public.compositefield cf WHERE cf.owner = OLD.owner) THEN
		RAISE EXCEPTION 'Composite variable % must have at least one field',OLD.owner USING ERRCODE='VD006';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_composite_variable_compositefield_d ON public.compositefield;
CREATE CONSTRAINT TRIGGER trigger_composite_variable_compositefield_d AFTER DELETE ON public.compositefield DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION public.constraint_composite_variable_compositefield_d();



------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_composite_variable_compositefield_i() -- check if a composite variable doesn't have a repeated fields
	RETURNS TRIGGER
AS
$$
DECLARE
	composite smallstring;
BEGIN
	IF NOT EXISTS (SELECT * FROM public.compositefield cf WHERE cf.owner = NEW.owner) THEN
		RAISE EXCEPTION 'Composite variable % must have at least one field',NEW.owner USING ERRCODE='VD006';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_composite_variable_compositefield_i ON public.compositefield;
CREATE CONSTRAINT TRIGGER trigger_composite_variable_compositefield_i AFTER INSERT ON public.compositefield DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION public.constraint_composite_variable_compositefield_i();

------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.check_value_domain() -- check if a value of a simple variable is of the same domain of the variable
	RETURNS TRIGGER
AS
$$
DECLARE
	domtype record;
	result public.real;
	bool boolean;
BEGIN
	IF EXISTS (SELECT * FROM public.variable v WHERE v.name = NEW.variable AND v.type_sc='composite') THEN
		RAISE EXCEPTION 'A composite variable can not have a value' USING ERRCODE='VD015';
	END IF;

	SELECT rd.domain, rd.min, rd.max, rd.step, rd.type INTO domtype FROM public.domain d, public.rangedomain rd, public.variable v WHERE v.name = NEW.variable AND d.name = v.domain AND d.name = rd.domain;
	IF (domtype IS NOT NULL) THEN
		IF (domtype.type = 'boolean') THEN
			IF ((NEW.value <> 0) AND (NEW.value <> 1)) THEN
				RAISE EXCEPTION 'Value of % must be %',NEW.variable,domtype.type USING ERRCODE='VD007';
			END IF;
		ELSIF (domtype.type = 'integer') THEN
			IF (NEW.value <> NEW.value::integer) THEN
				RAISE EXCEPTION 'Value of % must be %',NEW.variable,domtype.type USING ERRCODE='VD007';
			END IF;
		ELSIF (domtype.type = 'real') THEN
			result := (NEW.value-domtype.min)/domtype.step;
			IF ((NEW.value < domtype.min) OR (NEW.value > domtype.max) OR (result <> result::integer)) THEN
				RAISE EXCEPTION 'Value of % do not respect the range',NEW.variable USING ERRCODE='VD008';
			END IF;
		END IF;
	ELSE
		IF NOT EXISTS (SELECT * FROM public.enumeratevalue ev, public.variable v WHERE v.name = NEW.variable AND v.domain = ev.domain AND ev.id = NEW.value) THEN
			RAISE EXCEPTION 'Value of % must be in its enumerate domain %',NEW.variable,domtype USING ERRCODE='VD009';
		END IF;
	END IF;
	IF EXISTS (SELECT * FROM public.SimpleVariableValue svv WHERE svv.relcase=NEW.relcase AND svv.timestamp = NEW.timestamp AND svv.variable = NEW.variable AND svv.ordernum <> NEW.ordernum AND svv.value<>NEW.value) THEN
		RAISE EXCEPTION 'Value of % is already assigned in the state, can not have a different value',NEW.variable USING ERRCODE='VD019';
	END IF;
	RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_value_domain ON public.SimpleVariableValue;
CREATE TRIGGER trigger_value_domain BEFORE INSERT OR UPDATE OF value,variable ON public.SimpleVariableValue 
FOR EACH ROW EXECUTE FUNCTION public.check_value_domain();


------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_simplevariablevalue() --check that for each composite variable cv assigned: each mandatory field has a value and only simple variables in cv have a value.
--for each simple variable sv assigned: sv is the only simple variable that has a value
	RETURNS TRIGGER
AS
$$
DECLARE 
	type smallstring;
	mandfield record;
	value record;
BEGIN
	type := (SELECT v.type_sc FROM public.variable v WHERE v.name=NEW.variable);
	CREATE TEMPORARY TABLE simplevalues ON COMMIT DROP AS
		SELECT svv.variable
		FROM public.SimpleVariableValue svv 
		WHERE svv.relcase = NEW.relcase AND svv.timestamp = NEW.timestamp AND svv.ordernum = NEW.ordernum;
	IF NOT EXISTS (SELECT * FROM simplevalues) THEN
		RAISE EXCEPTION 'An assignment must have at least one value' USING ERRCODE='VD014';
	END IF;
	IF (type = 'composite') THEN
		FOR mandfield IN SELECT * FROM public.mandatory_tree(NEW.variable) LOOP
			IF NOT EXISTS(SELECT * FROM simplevalues sv WHERE sv.variable = mandfield.field) THEN
				RAISE EXCEPTION 'Each mandatory field of % must have a value',NEW.variable USING ERRCODE='VD012';
			END IF;
		END LOOP;
		FOR value IN SELECT * FROM simplevalues LOOP
			IF NOT (public.tree_root(NEW.variable,value.variable)) THEN
				RAISE EXCEPTION 'Only variables in % can have a value',NEW.variable USING ERRCODE='VD011';
			END IF;
		END LOOP;
	ELSE
		FOR value IN SELECT * FROM simplevalues LOOP
			IF (value.variable <> NEW.variable) THEN
				RAISE EXCEPTION 'Only % can have a value',NEW.variable USING ERRCODE='VD013';
			END IF;
		END LOOP;
	END IF;
	RETURN NULL;	
END;
$$
LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trigger_simplevariablevalue ON public.Assignment;
CREATE CONSTRAINT TRIGGER trigger_simplevariablevalue AFTER INSERT ON public.Assignment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION public.constraint_simplevariablevalue();


------------------------------------------------------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mandatory_tree(root smallstring) -- return the mandatory fields of a composite variable
RETURNS table(
		field smallstring
		)
AS
$$
BEGIN
	RETURN QUERY (WITH RECURSIVE fields AS (
		SELECT * FROM public.compositefield cf WHERE cf.owner=root AND cf.mandatory='t'
		UNION
		SELECT c.owner,c.field,c.mandatory FROM fields f,public.compositefield c WHERE f.field=c.owner AND c.mandatory = 't'
		) SELECT f.field FROM fields f);
END;
$$
LANGUAGE 'plpgsql';


------------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.tree_root(root smallstring, c_field smallstring) -- return true if the field is in the composite variable tree
	RETURNS boolean
AS
$$
BEGIN
	RETURN EXISTS (WITH RECURSIVE fields AS (
		SELECT * FROM public.compositefield cf WHERE cf.owner=root
		UNION
		SELECT c.owner,c.field,c.mandatory FROM fields f,public.compositefield c WHERE f.field=c.owner
		) SELECT * FROM fields f WHERE f.field = c_field);
END;
$$
LANGUAGE 'plpgsql';


------------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.same_root(firstfield smallstring, secondfield smallstring) -- return true if the field is in the composite variable tree
	RETURNS boolean
AS
$$
BEGIN
	CREATE TEMPORARY TABLE first_owners ON COMMIT DROP AS (WITH RECURSIVE fields AS (
		SELECT cf.owner FROM public.compositefield cf WHERE cf.field=firstfield
		UNION
		SELECT c.owner FROM fields f,public.compositefield c WHERE f.owner=c.field
		) SELECT f.owner FROM fields f WHERE NOT EXISTS (SELECT cf.field FROM public.compositefield cf WHERE cf.field=f.owner));

	CREATE TEMPORARY TABLE second_owners ON COMMIT DROP AS (WITH RECURSIVE fields AS (
		SELECT cf.owner FROM public.compositefield cf WHERE cf.field=secondfield
		UNION
		SELECT c.owner FROM fields f,public.compositefield c WHERE f.owner=c.field
		) SELECT f.owner FROM fields f WHERE NOT EXISTS (SELECT cf.field FROM public.compositefield cf WHERE cf.field=f.owner));
	RETURN EXISTS(SELECT * FROM first_owners fo, second_owners so WHERE fo.owner=so.owner);
END;
$$
LANGUAGE 'plpgsql';


------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.tree(root smallstring) -- return the tree fields of a composite variable
RETURNS table(
		owner smallstring,
		field smallstring,
		mandatory boolean
		)
AS
$$
BEGIN
	RETURN QUERY (WITH RECURSIVE fields AS (
		SELECT * FROM public.compositefield cf WHERE cf.owner=root
		UNION
		SELECT c.owner,c.field,c.mandatory FROM fields f,public.compositefield c WHERE f.field=c.owner
		) SELECT * FROM fields f);
END;
$$
LANGUAGE 'plpgsql';

------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_domain_completeanddisjoint() --check if a domain is complete and disjoint 
	RETURNS TRIGGER
AS
$$
DECLARE
	count integer;
BEGIN
	count := (SELECT count(*) FROM (
		SELECT domain FROM public.RangeDomain WHERE domain=NEW.name
		UNION ALL
		SELECT domain FROM public.EnumerateDomain WHERE domain=NEW.name
		) d);
	IF (count <> 1) THEN
		RAISE EXCEPTION 'Domain % is not complete and disjoint',NEW.name USING ERRCODE='VD016';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';


DROP TRIGGER IF EXISTS trigger_domain_completeanddisjoint ON public.domain;
CREATE CONSTRAINT TRIGGER trigger_domain_completeanddisjoint AFTER INSERT ON public.domain DEFERRABLE INITIALLY DEFERRED 
FOR EACH ROW EXECUTE FUNCTION public.constraint_domain_completeanddisjoint();

------------------------------------------------------------------------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION public.constraint_domain_rangedomain() --check if a rangedomain has correct values
	RETURNS TRIGGER
AS
$$
DECLARE
	
BEGIN
	IF (NEW.type = 'boolean') THEN
		IF ((NEW.min <> 0) OR (NEW.max <> 1) OR (NEW.step <> 1)) THEN
			RAISE EXCEPTION 'Incorrect attributes for the domain %',NEW.domain USING ERRCODE='VD018';
		END IF;
	ELSIF (NEW.type = 'integer') THEN
		IF ((NEW.min > NEW.max) OR (NEW.min <> NEW.min::integer) OR (NEW.max <> NEW.max::integer) OR (NEW.step <> NEW.step::integer)) THEN
			RAISE EXCEPTION 'Incorrect attributes for the domain %',NEW.domain USING ERRCODE='VD018';
		END IF;
	ELSIF (NEW.min > NEW.max) THEN
		RAISE EXCEPTION 'Incorrect attributes for the domain %',NEW.domain USING ERRCODE='VD018';
	END IF;
	RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';


DROP TRIGGER IF EXISTS trigger_domain_rangedomain ON public.rangedomain;
CREATE CONSTRAINT TRIGGER trigger_domain_rangedomain AFTER INSERT ON public.rangedomain DEFERRABLE INITIALLY DEFERRED 
FOR EACH ROW EXECUTE FUNCTION public.constraint_domain_rangedomain();














































