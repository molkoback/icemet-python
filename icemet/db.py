from icemet.file import FileStatus, File

import natsort
import pymysql

from collections import OrderedDict

__create_db_fmt__ = "CREATE DATABASE IF NOT EXISTS `{}`;"
__create_particles_table_fmt__ = "CREATE TABLE IF NOT EXISTS `{}`.`{}` ("\
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
"PRIMARY KEY (ID),"\
"INDEX (DateTime)"\
");"
__create_stats_table_fmt__ = "CREATE TABLE IF NOT EXISTS `{}`.`{}` ("\
"ID INT UNSIGNED NOT NULL AUTO_INCREMENT,"\
"DateTime DATETIME NOT NULL,"\
"LWC FLOAT NOT NULL,"\
"MVD FLOAT NOT NULL,"\
"Conc FLOAT NOT NULL,"\
"Frames INT UNSIGNED NOT NULL,"\
"Particles INT UNSIGNED NOT NULL,"\
"Temp FLOAT,"\
"Wind FLOAT,"\
"PRIMARY KEY (ID),"\
"INDEX (DateTime)"\
");"
__select_tables_fmt__ = "SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLES;"
__select_particles_fmt__ = "SELECT ID, DateTime, Sensor, Frame, Particle, X, Y, Z, EquivDiam, EquivDiamCorr, Circularity, DynRange, EffPxSz, SubX, SubY, SubW, SubH FROM `{}`.`{}` ORDER BY ID ASC;"
__select_stats_fmt__ = "SELECT ID, DateTime, LWC, MVD, Conc, Frames, Particles, Temp, Wind FROM `{}`.`{}` ORDER BY DateTime ASC;"
__insert_particles_fmt__ = "INSERT INTO `{}`.`{}` (ID, DateTime, Sensor, Frame, Particle, X, Y, Z, EquivDiam, EquivDiamCorr, Circularity, DynRange, EffPxSz, SubX, SubY, SubW, SubH) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
__insert_stats_fmt__ = "INSERT INTO `{}`.`{}` (ID, DateTime, LWC, MVD, Conc, Frames, Particles, Temp, Wind) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s);"
__update_particles_fmt__ = "UPDATE `{}`.`{}` SET DateTime=%s, Sensor=%s, Frame=%s, Particle=%s, X=%s, Y=%s, Z=%s, EquivDiam=%s, EquivDiamCorr=%s, Circularity=%s, DynRange=%s, EffPxSz=%s, SubX=%s, SubY=%s, SubW=%s, SubH=%s WHERE ID=%s;"
__update_stats_fmt__ = "UPDATE `{}`.`{}` SET DateTime=%s, LWC=%s, MVD=%s, Conc=%s, Frames=%s, Particles=%s, Temp=%s, Wind=%s WHERE ID=%s;"

class DBException(Exception):
	pass

class ParticlesRow:
	def __init__(self, **kwargs):
		self.__dict__ = {**self.__dict__, **kwargs}
	
	def __repr__(self):
		return "<ParticlesRow {}>".format(self.__dict__)
	
	def __setitem__(self, k, v):
		self.__dict__[k] = v
	
	def __getitem__(self, k):
		return self.__dict__[k]
	
	def get(self, k, default=None):
		return self.__dict__.get(k, default)
	
	def file(self):
		return File(sensor_id=self.Sensor, datetime=self.DateTime, frame=self.Frame, sub=self.Particle, status=FileStatus.NOTEMPTY)

class StatsRow:
	def __init__(self, **kwargs):
		self.__dict__ = {**self.__dict__, **kwargs}
	
	def __repr__(self):
		return "<StatsRow {}>".format(self.__dict__)
	
	def __setitem__(self, k, v):
		self.__dict__[k] = v
	
	def __getitem__(self, k):
		return self.__dict__[k]
	
	def get(self, k, default=None):
		return self.__dict__.get(k, default)
	
	def icingrate(self, obj):
		T = self.get("Temp")
		v = self.get("Wind")
		if T is None or v is None:
			return None
		return obj.icingrate(self.LWC, self.MVD, T, v)

class Database:
	def __init__(self, **kwargs):
		self.host = kwargs.get("host", "localhost")
		self.port = kwargs.get("port", 3306)
		self.user = kwargs.get("user", "root")
		self.password = kwargs.get("password", "")
		self._conn = pymysql.connect(
			host=self.host,
			port=self.port,
			user=self.user,
			password=self.password,
		)
	
	def __repr__(self):
		return "<Database {}@{}:{}>".format(self.user, self.host, self.port)
	
	def close(self):
		self._conn.close()
	
	def databases(self, table_prefixes=["particles", "stats"]):
		dict = {}
		with self._conn.cursor(cursor=pymysql.cursors.SSDictCursor) as curs:
			curs.execute(__select_tables_fmt__)
			for row in curs.fetchall_unbuffered():
				database = row["TABLE_SCHEMA"]
				table = row["TABLE_NAME"]
				
				for prefix in table_prefixes:
					if table.startswith(prefix):
						if not database in dict:
							dict[database] = []
						dict[database].append(table)
		
		alg = natsort.ns.IGNORECASE
		odict = OrderedDict(natsort.natsorted(dict.items(), alg=alg))
		for k, v in odict.items():
			odict[k] = natsort.natsorted(v, alg=alg)
		return odict
	
	def particles_databases(self):
		return self.databases(["particles"])
	
	def stats_databases(self):
		return self.databases(["stats"])
	
	def create_table(self, database, table):
		if table.startswith("particles"):
			table_fmt = __create_particles_table_fmt__
		elif table.startswith("stats"):
			table_fmt = __create_stats_table_fmt__
		else:
			raise DBException("Table names must start with 'particles' or `stats`")
		
		with self._conn.cursor() as curs:
			curs.execute(__create_db_fmt__.format(database))
			curs.execute(table_fmt.format(database, table))
		self._conn.commit()
	
	def select(self, query, cls=None):
		with self._conn.cursor(cursor=pymysql.cursors.SSDictCursor) as curs:
			curs.execute(query)
			for row in curs.fetchall_unbuffered():
				yield row if cls is None else cls(**row)
	
	def select_particles(self, database, table):
		return self.select(__select_particles_fmt__.format(database, table), cls=ParticlesRow)
	
	def select_stats(self, database, table):
		return self.select(__select_stats_fmt__.format(database, table), cls=StatsRow)
	
	def insert_particles(self, database, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M:%S.%f"), row.Sensor, row.Frame, row.Particle, row.X, row.Y, row.Z, row.EquivDiam, row.EquivDiamCorr, row.Circularity, row.DynRange, row.EffPxSz, row.SubX, row.SubY, row.SubW, row.SubH)
				curs.execute(__insert_particles_fmt__.format(database, table), t)
		self._conn.commit()
	
	def insert_stats(self, database, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M"), row.LWC, row.MVD, row.Conc, row.Frames, row.Particles, row.Temp, row.Wind)
				curs.execute(__insert_stats_fmt__.format(database, table), t)
		self._conn.commit()
	
	def update_particles(self, database, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M:%S.%f"), row.Sensor, row.Frame, row.Particle, row.X, row.Y, row.Z, row.EquivDiam, row.EquivDiamCorr, row.Circularity, row.DynRange, row.EffPxSz, row.SubX, row.SubY, row.SubW, row.SubH, row.ID)
				curs.execute(__update_particles_fmt__.format(database, table), t)
		self._conn.commit()
	
	def update_stats(self, database, table, rows):
		with self._conn.cursor() as curs:
			for row in rows:
				t = (row.DateTime.strftime("%Y-%m-%d %H:%M"), row.LWC, row.MVD, row.Conc, row.Frames, row.Particles, row.Temp, row.Wind, row.ID)
				curs.execute(__update_stats_fmt__.format(database, table), t)
		self._conn.commit()
