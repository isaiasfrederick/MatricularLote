WITH SalasPedagogiaModuloAtual AS (
	SELECT c.* FROM {course} c INNER JOIN {course_categories} cat ON cat.id = c.category
	WHERE cat.path ILIKE '%420/450%' -- Retorne aqui todos os courses do Bimestre/Semestre atual da Pedagogia
),
PolosPedagogiaModuloAtual AS (
	SELECT * FROM {groups} g WHERE g.courseid IN (SELECT id FROM SalasPedagogiaModuloAtual)
),
SalasPedagogia AS (
	SELECT c.* FROM {course} c INNER JOIN {course_categories} cat ON cat.id = c.category
	WHERE cat.path ILIKE '%420/450%'
),
MatriculadosPedagogia AS (
	SELECT 
    u.id AS userid,
    u.firstname,
    u.lastname,
    u.email,
    c.id AS courseid,
    c.fullname AS coursename
	FROM {user_enrolments} ue
	JOIN {enrol} e ON ue.enrolid = e.id
	JOIN {user} u ON ue.userid = u.id
	JOIN {course} c ON e.courseid = c.id
	WHERE c.id IN (SELECT id FROM SalasPedagogia)
	AND u.deleted = 0
),
MatriculadosPedagogiaModuloAtual AS (
	SELECT 
    u.id AS userid,
    u.firstname,
    u.lastname,
    u.email,
    c.id AS courseid,
    c.fullname AS coursename
	FROM {user_enrolments} ue
	JOIN {enrol} e ON ue.enrolid = e.id
	JOIN {user} u ON ue.userid = u.id
	JOIN {course} c ON e.courseid = c.id
	WHERE c.id IN (SELECT id FROM SalasPedagogiaModuloAtual)
	AND u.deleted = 0
),
UsuarioAgrupadoPadraoTmp AS (
	SELECT
		ped.userid,
		g."name" AS nome_polo,
  		COUNT(*) AS "freq_polo"
	FROM
		MatriculadosPedagogia ped INNER JOIN
		{groups_members} m ON m.userid = ped.userid INNER JOIN
		{groups} g ON g.courseid = ped."courseid" AND m.groupid = g.id
	WHERE g.name ILIKE '%P_lo%'
	GROUP BY ped.userid, g."name"
),
UsuarioAgrupadoPadrao AS (
	SELECT
	  userid,
	  string_agg(nome_polo, ', ' ORDER BY nome_polo) "todos_polos",
	  (SELECT nome_polo
		 FROM UsuarioAgrupadoPadraoTmp e2
		 WHERE e2.userid = e.userid
		 ORDER BY "freq_polo" DESC, nome_polo
		 LIMIT 1) AS nome_polo,
  		COUNT(DISTINCT nome_polo) AS "total_polos"
	FROM UsuarioAgrupadoPadraoTmp e
	GROUP BY userid
),
UsuarioAgrupadoPadraoBkp AS (
	SELECT
		ped.userid,
		(array_agg(g."name" ORDER BY g."name"))[1] AS nome_polo,
		STRING_AGG(g."name", ', ') "todos_polos",
  	COUNT(DISTINCT g."name") "total_polos"
	FROM
		MatriculadosPedagogia ped INNER JOIN
		{groups_members} m ON m.userid = ped.userid INNER JOIN
		{groups} g ON g.courseid = ped."courseid" AND m.groupid = g.id
	WHERE g.name ILIKE '%P_lo%'
	GROUP BY ped.userid
	HAVING COUNT(DISTINCT g."name") > 1
)

SELECT
	ped_atual.userid,
	ped_atual.firstname, ped_atual.lastname,
	ped_atual.courseid,
	ped_atual.coursename,
	padrao.nome_polo "polo_padrao",
	padrao.todos_polos,
	padrao.total_polos,
	polos_modulo_atual.name "polo_sala",
	polos_modulo_atual.id "polo_id"
FROM MatriculadosPedagogiaModuloAtual ped_atual 
INNER JOIN UsuarioAgrupadoPadrao padrao ON ped_atual.userid = padrao.userid 
INNER JOIN PolosPedagogiaModuloAtual polos_modulo_atual 
	ON regexp_replace(
         regexp_replace(
           regexp_replace(
             regexp_replace(
               regexp_replace(
                 regexp_replace(
                   regexp_replace(polos_modulo_atual.name, '[áàâãäå]', 'a', 'gi'),
                 '[éèêë]', 'e', 'gi'),
               '[íìîï]', 'i', 'gi'),
             '[óòôõö]', 'o', 'gi'),
           '[úùûü]', 'u', 'gi'),
         '[ñ]', 'n', 'gi'),
       '[ç]', 'c', 'gi') =
regexp_replace(
         regexp_replace(
           regexp_replace(
             regexp_replace(
               regexp_replace(
                 regexp_replace(
                   regexp_replace(nome_polo, '[áàâãäå]', 'a', 'gi'),
                 '[éèêë]', 'e', 'gi'),
               '[íìîï]', 'i', 'gi'),
             '[óòôõö]', 'o', 'gi'),
           '[úùûü]', 'u', 'gi'),
         '[ñ]', 'n', 'gi'),
       '[ç]', 'c', 'gi') AND polos_modulo_atual.courseid = ped_atual.courseid
WHERE ped_atual.courseid IN (1355, 1358) AND total_polos > 1
