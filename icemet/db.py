from icemet.file import File

import natsort
import pymysql

__create_db_fmt__ = "CREATE DATABASE {}"
__create_particles_table_fmt__ = "CREATE TABLE {} ("\
"ID INT UNSIGNED NOT NULL AUTO_INCREMENT,"\
"DateTime DATETIME(3) NOT NULL,"\
"Sensor TINYINT UNSIGNED NOT NULL,"\
"Frame INT UNSIGNED NOT NULL,"\
"Particle INT UNSIGNED NOT NULL,"\
"X FLOAT NOT NULL,"\
"Y FLOAT NOT NULL,"\
"Z FLOAT NOT NULL,"\
"EquivDiam FLOAT NOT NULL,"\
"EquivDiamCorr FLOAT NOT NULL,"\
"Circularity FLOAT NOT NULL,"\
"DynRange TINYINT UNSIGNED NOT NULL,"\
"EffPxSz FLOAT NOT NULL,"\
"SubX INT UNSIGNED NOT NULL,"\
"SubY INT UNSIGNED NOT NULL,"\
"SubW INT UNSIGNED NOT NULL,"\
"SubH INT UNSIGNED NOT NULL,"\
"PRIMARY KEY (ID)"\
")"
__create_stats_table_fmt__ = "CREATE TABLE {} ("\
"ID INT UNSIGNED NOT NULL AUTO_INCREMENT,"\
"DateTime DATETIME NOT NULL,"\
"LWC FLOAT NOT NULL,"\
"MVD FLOAT NOT NULL,"\
"Conc FLOAT NOT NULL,"\
"Frames INT UNSIGNED NOT NULL,"\
"Particles INT UNSIGNED NOT NULL,"\
"PRIMARY KEY (ID)"\
")"
__select_tables_fmt__ = "SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLES"
__select_particles_fmt__ = "SELECT ID, DateTime, Sensor, Frame, Particle, X, Y, Z, EquivDiam, EquivDiamCorr, Circularity, DynRange, EffPxSz, SubX, SubY, SubW, SubH FROM {} ORDER BY ID ASC"
__select_stats_fmt__ = "SELECT ID, DateTime, LWC, MVD, Conc, Frames, Particles FROM {} ORDER BY DateTime ASC"
__insert_particles_fmt__ = "INSERT INTO {} (ID, DateTime, Sensor, Frame, Particle, X, Y, Z, EquivDiam, EquivDiamCorr, Circularity, DynRange, EffPxSz, SubX, SubY, SubW, SubH) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
__insert_stats_fmt__ = "INSERT INTO {} (ID, DateTime, LWC, MVD, Conc, Frames, Particles) VALUES (NULL, %s, %s, %s, %s, %s, %s)"

class DBException(Exception):
	pass

class Database:
	def __init__(self, **kwargs):
		self.host = kwargs.get("host", "localhost")
		self.port = kwargs.get("port", 3306)
		self.user = kwargs.get("user", "root")
		self.passwd = kwargs.get("passwd", "")
		self._conn = None
	
	def open(self):
		self._conn = pymysql.connect(
			host=self.host,
			port=self.port,
			user=self.user,
			password=self.passwd,
			cursorclass=pymysql.cursors.DictCursor
		)
	
	def close(self):
		self._conn.close()
	
	def tables(self):
		ts = []
		with self._conn.cursor(cursor=pymysql.cursors.SSDictCursor) as curs:
			curs.execute(__select_tables_fmt__)
			for row in curs.fetchall_unbuffered():
				table = "{}.{}".format(row["TABLE_SCHEMA"], row["TABLE_NAME"])
				name = row["TABLE_NAME"]
				if name.startswith("particles") or name.startswith("stats"):
					ts.append("{}.{}".format(row["TABLE_SCHEMA"], name))
		return natsort.natsorted(ts, alg=natsort.ns.IGNORECASE)
	
	def _create_table(self, table, db_fmt, table_fmt):
		tables = self.tables()
		if not table in tables:
			with self._conn.cursor() as curs:
				db, t = table.split(".", 1)
				if not db in [table.split(".")[0] for table in tables]:
					curs.execute(db_fmt.format(db))
				curs.execute(table_fmt.format(table))
			self._conn.commit()
	
	def create_particles_table(self, table):
		if not table.split(".", 1)[-1].startswith("particles"):
			raise DBException("Particle table names must start with 'particles'")
		self._create_table(table, __create_db_fmt__, __create_particles_table_fmt__)
	
	def create_stats_table(self, table):
		if not table.split(".", 1)[-1].startswith("stats"):
			raise DBException("Statistic table names must start with 'stats'")
		self._create_table(table, __create_db_fmt__, __create_stats_table_fmt__)
	
	def select_particles(self, table):
		with self._conn.cursor(cursor=pymysql.cursors.SSDictCursor) as curs:
			curs.execute(__select_particles_fmt__.format(table))
			for row in curs.fetchall_unbuffered():
				yield ParticleRow(**row)
	
	def select_stats(self, table):
		with self._conn.cursor(cursor=pymysql.cursors.SSDictCursor) as curs:
			curs.execute(__select_stats_fmt__.format(table))
			for row in curs.fetchall_unbuffered():
				yield StatsRow(**row)
	
	def insert_particles(self, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M:%S.%f"), row.Sensor, row.Frame, row.Particle, row.X, row.Y, row.Z, row.EquivDiam, row.EquivDiamCorr, row.Circularity, row.DynRange, row.EffPxSz, row.SubX, row.SubY, row.SubW, row.SubH)
				curs.execute(__insert_particles_fmt__.format(table), t)
		self._conn.commit()
	
	def insert_stats(self, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M"), row.LWC, row.MVD, row.Conc, row.Frames, row.Particles)
				curs.execute(__insert_stats_fmt__.format(table), t)
		self._conn.commit()

class ParticleRow:
	def __init__(self, **kwargs):
		self.__dict__ = {**self.__dict__, **kwargs}
	
	def file(self):
		return File(self.Sensor, self.DateTime, self.Frame, sub=self.Particle)

class StatsRow:
	def __init__(self, **kwargs):
		self.__dict__ = {**self.__dict__, **kwargs}
