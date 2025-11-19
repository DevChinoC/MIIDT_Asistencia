CREATE SCHEMA asistencia_biometrica;

CREATE  TABLE areas_conocimiento ( 
	id                   INT    NOT NULL AUTO_INCREMENT  PRIMARY KEY,
	nombre               VARCHAR(100)    NOT NULL   ,
	created_at           TIMESTAMP  DEFAULT (CURRENT_TIMESTAMP)     ,
	updated_at           TIMESTAMP  DEFAULT (CURRENT_TIMESTAMP) ON UPDATE CURRENT_TIMESTAMP    ,
	CONSTRAINT nombre UNIQUE ( nombre ) 
 ) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE  TABLE generaciones ( 
	id                   INT    NOT NULL AUTO_INCREMENT  PRIMARY KEY,
	nombre               VARCHAR(64)    NOT NULL   ,
	created_at           TIMESTAMP  DEFAULT (CURRENT_TIMESTAMP)     ,
	updated_at           TIMESTAMP  DEFAULT (CURRENT_TIMESTAMP) ON UPDATE CURRENT_TIMESTAMP    ,
	CONSTRAINT nombre UNIQUE ( nombre ) 
 ) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE  TABLE teachers ( 
	id                   BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT  PRIMARY KEY,
	employee_number      VARCHAR(255)   COLLATE utf8mb4_unicode_ci    ,
	name                 VARCHAR(255)   COLLATE utf8mb4_unicode_ci NOT NULL   ,
	phone                VARCHAR(10)   COLLATE utf8mb4_unicode_ci    ,
	email                VARCHAR(255)   COLLATE utf8mb4_unicode_ci    ,
	created_at           TIMESTAMP       ,
	updated_at           TIMESTAMP       ,
	CONSTRAINT teachers_employee_number_unique UNIQUE ( employee_number ) ,
	CONSTRAINT teachers_phone_unique UNIQUE ( phone ) ,
	CONSTRAINT teachers_email_unique UNIQUE ( email ) 
 ) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE  TABLE alumnos ( 
	id                   BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT  PRIMARY KEY,
	email                VARCHAR(64)    NOT NULL   ,
	matricula            BIGINT UNSIGNED   NOT NULL   ,
	nombre               VARCHAR(64)    NOT NULL   ,
	apellido_paterno     VARCHAR(64)    NOT NULL   ,
	apellido_materno     VARCHAR(64)    NOT NULL   ,
	huella_digital       BLOB       ,
	email_verified_at    TIMESTAMP       ,
	created_at           TIMESTAMP       ,
	updated_at           TIMESTAMP       ,
	generacion           VARCHAR(64)       ,
	asesor               VARCHAR(64)       ,
	area_conocimiento    VARCHAR(64)       ,
	carrera              VARCHAR(64)       ,
	rol                  VARCHAR(16)       ,
	asesor_id            BIGINT UNSIGNED      
 ) ENGINE=InnoDB AUTO_INCREMENT=83 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX fk_alumnos_teachers ON alumnos ( asesor_id );

CREATE  TABLE registro_asistencias ( 
	id                   BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT  PRIMARY KEY,
	alumno_id            BIGINT UNSIGNED   NOT NULL   ,
	asistencia           DATE    NOT NULL   ,
	hora_entrada         TIME    NOT NULL   ,
	hora_salida          TIME       ,
	created_at           TIMESTAMP       ,
	updated_at           TIMESTAMP       
 ) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX fk_registro_asistencias_alumnos ON registro_asistencias ( alumno_id );

ALTER TABLE alumnos ADD CONSTRAINT fk_alumnos_teachers FOREIGN KEY ( asesor_id ) REFERENCES teachers( id ) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE registro_asistencias ADD CONSTRAINT fk_registro_asistencias_alumnos FOREIGN KEY ( alumno_id ) REFERENCES alumnos( id ) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE teachers COMMENT 'Tabla de maestros';

ALTER TABLE teachers MODIFY employee_number VARCHAR(255)     COMMENT 'Numero de empleado';

ALTER TABLE teachers MODIFY name VARCHAR(255)  NOT NULL   COMMENT 'Nombre del profesor';

ALTER TABLE teachers MODIFY phone VARCHAR(10)     COMMENT 'Telefono del profesor';

ALTER TABLE teachers MODIFY email VARCHAR(255)     COMMENT 'Correo del profesor';

INSERT INTO areas_conocimiento( id, nombre, created_at, updated_at ) VALUES ( 1, 'TIC''S', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO areas_conocimiento( id, nombre, created_at, updated_at ) VALUES ( 2, 'CSR', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO areas_conocimiento( id, nombre, created_at, updated_at ) VALUES ( 3, 'GEO', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO generaciones( id, nombre, created_at, updated_at ) VALUES ( 1, '7a Generación (2020-2022)', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO generaciones( id, nombre, created_at, updated_at ) VALUES ( 3, '9a Generación (2022-2024)', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO generaciones( id, nombre, created_at, updated_at ) VALUES ( 4, '10a Generación (2023-2025)', '2025-08-22 03.18.17 p. m.', '2025-08-22 03.18.17 p. m.');
INSERT INTO generaciones( id, nombre, created_at, updated_at ) VALUES ( 10, '11a Generación (2025)', '2025-08-25 07.15.22 a. m.', '2025-08-25 07.16.08 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 1, '12345', 'Rocío Nayelly Ramos Bernal', '5434763246', 'rocionayeli@uagro.mx', '2024-12-24 10.29.23 a. m.', '2024-12-24 10.30.22 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 2, '12346', 'Alma Villaseñor Franco', '1234567891', 'almavilla@uagro.mx', '2024-12-24 10.31.02 a. m.', '2024-12-24 10.31.02 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 3, '12347', 'Antonio Alarcón Paredes', '1234567892', 'antonio@uagro.mx', '2024-12-24 10.32.07 a. m.', '2024-12-24 10.32.31 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 4, '12348', 'Gustavo Adolfo Alonso Silverio', '1234567893', 'gustavo@uagro.mx', '2024-12-24 10.32.52 a. m.', '2024-12-24 10.32.52 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 5, '12349', 'Roberto Arroyo Matus', '1234567894', 'roberto@uagro.mx', '2024-12-25 02.44.02 a. m.', '2024-12-25 02.44.02 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 6, '03180', 'Arnulfo Catalán Villegas', '7474707330', '03180@uagro.mx', '2024-12-25 02.47.07 a. m.', '2024-12-25 02.48.08 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 7, '03181', 'René Edmundo Cuevas Valencia', '7442541529', 'reneecuevas@uagro.mx', '2024-12-25 02.51.13 a. m.', '2024-12-25 02.51.46 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 8, '03182', 'Esteban Rogelio Guinto Herrera', '7471150645', 'erguinto@uagro.mx', '2024-12-25 02.52.55 a. m.', '2024-12-25 02.52.55 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 9, '03183', 'Sulpicio Sánchez Tizapa', '7471360309', 'sstizapa@uagro.mx', '2024-12-25 02.55.51 a. m.', '2024-12-25 02.56.14 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 10, '01', 'René Vázquez Jiménez', '7471360302', 'rvazquez@uagro.mx', '2024-12-25 02.58.16 a. m.', '2024-12-25 02.58.32 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 11, '02', 'Gerardo Altamirano de la Cruz', '7471360123', 'gerardocruz@uagro.mx', '2024-12-25 03.01.29 a. m.', '2024-12-25 03.01.29 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 12, null, 'Elías Jesús Ventura Molina', null, null, '2024-12-25 03.10.36 a. m.', '2024-12-25 03.10.54 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 13, null, 'Manuel Ignacio Ruz Vargas', null, null, '2024-12-25 03.11.15 a. m.', '2024-12-25 03.11.15 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 14, null, 'Adrián Urióstegui Flores', null, null, '2024-12-25 03.11.49 a. m.', '2024-12-25 03.12.05 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 15, null, 'José Mauricio Galeana Pizaña', null, null, '2024-12-25 03.12.23 a. m.', '2024-12-25 03.12.37 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 16, null, 'Angelino Feliciano Morales', null, null, '2024-12-25 03.12.50 a. m.', '2024-12-25 03.12.50 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 17, null, 'Wendy Romero Rojas', null, null, '2024-12-25 03.13.16 a. m.', '2024-12-25 03.13.16 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 18, null, 'Alejandro Durán Herrera', null, null, '2024-12-25 03.13.51 a. m.', '2024-12-25 03.14.06 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 19, null, 'Imelda López Valle', null, null, '2024-12-25 03.14.21 a. m.', '2024-12-25 03.14.49 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 20, null, 'Yesid Tibaquira Cortes', null, null, '2024-12-25 03.15.04 a. m.', '2024-12-25 03.15.04 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 21, null, 'Alfredo Cuevas Sandoval', null, null, '2024-12-25 03.15.39 a. m.', '2024-12-25 03.15.39 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 22, null, 'Cesar Antonio Juárez Alvarado', null, null, '2024-12-25 03.16.08 a. m.', '2024-12-25 03.16.23 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 23, null, 'Román M. Isidro Alvarado', null, null, '2024-12-25 03.16.47 a. m.', '2024-12-25 03.17.02 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 24, null, 'Adrián García Bruzón', null, null, '2024-12-25 03.17.22 a. m.', '2024-12-25 03.17.37 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 25, null, 'Daniel José Vega Nieva', null, null, '2024-12-25 03.17.49 a. m.', '2024-12-25 03.18.05 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 26, null, 'Patricia Arrogante Funes', null, null, '2024-12-25 03.18.17 a. m.', '2024-12-25 03.18.17 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 27, null, 'Guadalupe Rebeca Granados Martínez', null, null, '2024-12-25 03.18.54 a. m.', '2024-12-25 03.19.07 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 28, null, 'Carlos Salgado Galarza', null, null, '2024-12-25 03.19.17 a. m.', '2024-12-25 03.19.17 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 29, null, 'Rafael German Urban Lamadrid', null, null, '2024-12-25 03.19.42 a. m.', '2024-12-25 03.19.42 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 30, null, 'Juan Miguel Hernández Bravo', null, null, '2024-12-25 03.20.12 a. m.', '2024-12-25 03.20.26 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 31, null, 'Fernando Pérez Escamirosa', null, null, '2024-12-25 03.20.40 a. m.', '2024-12-25 03.20.53 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 32, null, 'David González Maxinez', null, null, '2024-12-25 03.21.57 a. m.', '2024-12-25 03.22.22 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 33, null, 'Francisco Ham Salgado', null, null, '2024-12-25 03.22.58 a. m.', '2024-12-25 03.22.58 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 34, 'None', 'Saúl Esteban López Ríos', 'None', 'None', '2024-12-25 03.23.21 a. m.', '2025-08-24 05.45.54 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 35, null, 'Eduardo Torres Ramírez', null, null, '2024-12-25 03.23.52 a. m.', '2024-12-25 03.24.07 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 36, null, 'Yanchuang Zhao', null, null, '2024-12-25 03.24.18 a. m.', '2024-12-25 03.24.18 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 37, null, 'Fátima Arrogante Funes', null, null, '2024-12-25 03.24.48 a. m.', '2024-12-25 03.25.04 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 38, null, 'Oscar Frausto Martínez', null, null, '2024-12-25 03.25.19 a. m.', '2024-12-25 03.25.34 a. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 39, null, 'Norma Arroyo Domínguez', null, null, '2025-01-02 09.48.58 p. m.', '2025-01-02 09.49.46 p. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 40, null, 'Iris Paola Guzmán Guzmán', null, null, '2025-01-03 07.33.13 p. m.', '2025-01-03 07.33.28 p. m.');
INSERT INTO teachers( id, employee_number, name, phone, email, created_at, updated_at ) VALUES ( 41, null, 'Rosendo Guzmán Nogueda', null, null, '2025-01-03 07.39.38 p. m.', '2025-01-03 07.39.59 p. m.');
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 58, '15217613@uagro.mx', 15217613, 'Carlos', 'Álvarez', 'Carmona', 'Right-click to view content', null, '2025-08-13 04.14.56 p. m.', '2025-08-19 09.20.47 a. m.', '10a Generación (2023-2025)', 'René Edmundo Cuevas Valencia', 'TIC''S', '', null, 7);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 59, '15197682@uagro.mx', 15197682, 'Blanca Esthela', 'Rodríguez', 'Martínez', 'Right-click to view content', null, '2025-08-13 04.17.28 p. m.', '2025-08-19 09.21.23 a. m.', '10a Generación (2023-2025)', 'Esteban Rogelio Guinto Herrera', 'CSR', '', null, 8);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 60, '10094539@uagro.mx', 10094539, 'Fausto Sebastián', 'Peralta', 'Catalán', 'Right-click to view content', null, '2025-08-13 04.20.26 p. m.', '2025-08-19 09.21.52 a. m.', '10a Generación (2023-2025)', 'Saúl Esteban López Ríos', 'CSR', '', null, 34);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 61, '08054115@uagro.mx', 8054115, 'Briseyda', 'Carachure', 'Nava', 'Right-click to view content', null, '2025-08-14 04.05.29 a. m.', '2025-08-19 09.22.09 a. m.', '10a Generación (2023-2025)', 'Alma Villaseñor Franco', 'GEO', '', null, 2);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 62, '23500770@uagro.mx', 23500770, 'Janet Guadalupe', 'Nava', 'Rendón', 'Right-click to view content', null, '2025-08-14 04.07.24 a. m.', '2025-08-19 09.22.34 a. m.', '10a Generación (2023-2025)', 'Arnulfo Catalán Villegas', 'TIC''S', '', null, 6);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 63, '13394735@uagro.mx', 13394735, 'Edilia', 'Morales', 'Mercado', 'Right-click to view content', null, '2025-08-14 04.09.04 a. m.', '2025-08-19 09.23.29 a. m.', '10a Generación (2023-2025)', 'Gerardo Altamirano de la Cruz', 'CSR', '', null, 11);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 64, '12486654@uagro.mx', 12486654, 'Heber', 'Navarro', 'López ', 'Right-click to view content', null, '2025-08-14 04.11.08 a. m.', '2025-08-19 09.23.44 a. m.', '10a Generación (2023-2025)', 'Esteban Rogelio Guinto Herrera', 'CSR', '', null, 8);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 65, '16357403@uagro.mx', 16357403, 'Jesús Alberto', 'Ramírez', 'Santos', 'Right-click to view content', null, '2025-08-14 04.12.46 a. m.', '2025-08-19 09.24.01 a. m.', '10a Generación (2023-2025)', 'Roberto Arroyo Matus', 'CSR', '', null, 5);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 66, '23501187@uagro.mx', 23501187, 'Raúl', 'Ramírez', 'Romero', 'Right-click to view content', null, '2025-08-14 04.15.26 a. m.', '2025-08-19 09.24.45 a. m.', '10a Generación (2023-2025)', 'Rocío Nayelly Ramos Bernal', 'GEO', '', null, 1);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 67, '12306175@uagro.mx', 12306175, 'Benjamin', 'Jiménez', 'Pérez', 'Right-click to view content', null, '2025-08-14 04.16.31 a. m.', '2025-08-19 09.25.04 a. m.', '10a Generación (2023-2025)', 'René Vázquez Jiménez', 'GEO', '', null, 10);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 68, '23500377@uagro.mx', 23500377, 'Israel Edgar', 'Nieto', 'Granados', 'Right-click to view content', null, '2025-08-14 04.18.04 a. m.', '2025-08-19 09.25.18 a. m.', '10a Generación (2023-2025)', 'Antonio Alarcón Paredes', 'TIC''S', '', null, 3);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 69, '15321282@uagro.mx', 15321282, 'Miriam', 'Liborio', 'Vicente', 'Right-click to view content', null, '2025-08-14 04.22.02 a. m.', '2025-08-19 09.25.53 a. m.', '10a Generación (2023-2025)', 'Rocío Nayelly Ramos Bernal', 'GEO', '', null, 1);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 70, '23500279@uagro.mx', 23500279, 'Ángel', 'Ríos', 'Gamiño', 'Right-click to view content', null, '2025-08-14 04.23.14 a. m.', '2025-08-19 09.26.07 a. m.', '10a Generación (2023-2025)', 'Gustavo Adolfo Alonso Silverio', 'CSR', '', null, 4);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 71, '23500767@uagro.mx', 23500767, 'Samir', 'Hernández', 'Hernández', 'Right-click to view content', null, '2025-08-14 04.25.15 a. m.', '2025-08-19 09.26.45 a. m.', '10a Generación (2023-2025)', 'Sulpicio Sánchez Tizapa', 'CSR', '', null, 9);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 72, '15468631@uagro.mx', 15468631, 'Uriel', 'Damián', 'Montiel', 'Right-click to view content', null, '2025-08-14 04.27.06 a. m.', '2025-08-19 09.26.58 a. m.', '10a Generación (2023-2025)', 'Gustavo Adolfo Alonso Silverio', 'TIC''S', '', null, 4);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 73, '11108967@uagro.mx', 11108967, 'Josué', 'Rendón', 'Guevara', 'Right-click to view content', null, '2025-08-14 04.28.28 a. m.', '2025-08-19 09.27.13 a. m.', '10a Generación (2023-2025)', 'Gerardo Altamirano de la Cruz', 'CSR', '', null, 11);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 74, '13337176@uagro.mx', 13337176, 'Jorge Irving', 'Cristóbal', 'Pichardo', 'Right-click to view content', null, '2025-08-14 04.29.59 a. m.', '2025-08-19 09.27.29 a. m.', '10a Generación (2023-2025)', 'René Edmundo Cuevas Valencia', 'TIC''S', '', null, 7);
-- INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 75, 'eliasted16@gmail.com', 16270016, 'Eliase', 'Evangelista', 'Lucas', 'application/octet-stream', null, '2025-08-14 04.07.05 p. m.', '2025-08-16 04.08.00 p. m.', '', '', '', '', null, null);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 76, 'reneecuevas@uagro.mx', 12654, 'Rene Edmundo', 'Cuevas', 'Valencia', 'application/octet-stream', null, '2025-08-15 04.49.27 a. m.', null, null, null, null, null, null, null);
-- INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 77, 'eleverevangelista4@gmail.com', 25520041, 'Elver Saul', 'Evangelista', 'Villanueva', 'application/octet-stream', null, '2025-08-15 02.46.29 p. m.', null, null, null, null, null, null, null);
-- INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 78, 'eliasclassi16@gmail.com', 16270016, 'Elías', 'Evangelista', 'Villanueva', 'application/octet-stream', null, '2025-08-15 04.35.24 p. m.', '2025-08-19 09.13.31 a. m.', '10a Generación (2023-2025)', 'René Edmundo Cuevas Valencia', 'TIC''S', 'Ing. Computación', null, 7);
-- INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 79, 'eliasted16@gmail.com', 5454646, 'Fulano', 'Lopex', 'Pin', 'application/octet-stream', null, '2025-08-18 04.06.00 p. m.', null, '10a Generación (2023-2025)', 'René Edmundo Cuevas Valencia', 'TIC''S', 'Ing. Computación', null, 7);
-- INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 81, 'ejemplo@gmail.com', 442464, 'Mengano', 'Tañi', 'Inle', 'application/octet-stream', null, '2025-08-19 05.28.38 a. m.', '2025-08-22 01.20.59 p. m.', '10a Generación (2023-2025)', '', 'TIC''S', 'Ing. Computacion', null, null);
INSERT INTO alumnos( id, email, matricula, nombre, apellido_paterno, apellido_materno, huella_digital, email_verified_at, created_at, updated_at, generacion, asesor, area_conocimiento, carrera, rol, asesor_id ) VALUES ( 82, 'torreschegue@gmail.com', 13005354, 'Cristian Omar', 'Torres', 'Chegue', 'application/octet-stream', null, '2025-08-25 07.33.44 a. m.', null, '11a Generación (2025)', 'Arnulfo Catalán Villegas', 'TIC''S', 'Computacion', null, 6);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 59, 75, '2025-08-14', '22:17:10', '22:51:29', '2025-08-14 04.17.10 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 60, 76, '2025-08-15', '10:50:28', '11:07:16', '2025-08-15 04.50.28 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 61, 78, '2025-08-15', '22:37:20', '22:39:05', '2025-08-15 04.37.20 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 62, 75, '2025-08-16', '22:03:12', '22:09:43', '2025-08-16 04.03.12 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 63, 78, '2025-08-18', '19:34:00', '20:30:10', '2025-08-18 01.34.00 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 64, 75, '2025-08-18', '19:56:36', '21:04:44', '2025-08-18 01.56.36 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 65, 77, '2025-08-18', '19:59:08', '20:53:09', '2025-08-18 01.59.08 p. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 66, 78, '2025-08-19', '15:28:29', '16:06:02', '2025-08-19 09.28.29 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 67, 79, '2025-08-19', '15:29:23', '16:06:19', '2025-08-19 09.29.23 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 68, 77, '2025-08-19', '16:07:45', '19:39:40', '2025-08-19 10.07.45 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 69, 81, '2025-08-20', '11:29:04', '11:33:50', '2025-08-20 05.29.04 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 70, 75, '2025-08-20', '11:34:20', '11:39:05', '2025-08-20 05.34.20 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 71, 79, '2025-08-21', '15:37:50', '17:14:18', '2025-08-21 09.37.50 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 72, 78, '2025-08-21', '15:38:03', '18:02:02', '2025-08-21 09.38.03 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 73, 75, '2025-08-21', '15:38:14', '17:06:23', '2025-08-21 09.38.14 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 74, 77, '2025-08-21', '15:38:29', '17:14:52', '2025-08-21 09.38.29 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 75, 79, '2025-08-22', '11:35:21', '11:40:44', '2025-08-22 05.35.21 a. m.', null);
INSERT INTO registro_asistencias( id, alumno_id, asistencia, hora_entrada, hora_salida, created_at, updated_at ) VALUES ( 76, 82, '2025-08-25', '13:34:02', '13:34:24', '2025-08-25 07.34.02 a. m.', null);
