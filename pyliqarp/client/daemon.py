class PoliqarpDaemonClient:
	"""
		Klasa umożliwiająca wykonywanie zapytań do serwera poliqarpd. Więcej na
		temat formatu zapytań w dokumentacji do poliqarp'a.
	"""

	def __init__(self):
		pass
	
	def connect(self, host = "localhost", port = 4567):
		"""
			Łączenie z serwerem poliqarpd.

			@param host	- komputer, z którym się łączyć (domyślnie: localhost)
			@param port	- port połączenia (domyślnie: 4567)
		"""
		self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		try:
			self.__conn.connect((host, port))
		except socket.error, (code, error):
			print error
			return False
		
		self.__conn.settimeout(1.0)

		return True
	
	def close(self):
		"""	Zamknięcie połączenia. """
		self.__conn.close()

	def __command(self, cmd, expected = 0):
		self.__conn.send(cmd + "\n")

		buffer	= ""
		lines	= []
		status	= None

		while (len(lines) < expected) or status == None:
			try:	l = self.__conn.recv(4096)
			except:
				l = ""
				print ".", 

			if l.startswith("R OK"):
				l = l[4:]
				status = True

			if l.startswith("R ERR"):
				l = l[5:]
				status = False

			buffer += l

			if buffer.endswith("\n"):
				lines += buffer.strip().splitlines()
				buffer = ""

		res = [ l.split() for l in lines ]

		if not status:
			res = False
		elif status and res == []:
			res = True

		return res

	def session_begin(self):
		"""	Otwarcie sesji z serwerem. """
		return self.__command("MAKE-SESSION CLIENT")

	def session_configure(self, dict, lctx_width = 5, rctx_width = 5):
		"""
			Konfiguracja sesji.

			@param dict 		- słownik do zadawania zapytań
			@param lctx_width	- szerokość lewego kontekstu
			@param rctx_width	- szerokość prawego kontekstu

			@returns True jeśli się powiodło, w p.p. False
		"""
		self.__command("SET left-context-width %d" % lctx_width)
		self.__command("SET right-context-width %d" % rctx_width)
		self.__command("SET wide-context-width 50")
		self.__command("SET retrieve-lemmata 0110")
		self.__command("SET retrieve-tags 0110")
		self.__command("SET query-flags 0011")
		self.__command("SET disamb 1")

		if self.__command("OPEN " + dict, 1)[0][1] == "OPENFAIL":
			print "%s: no such dictionary." % dict
			return False

		self.__command("METADATA-TYPES", 1)

		return True

	def query(self, query, bufsize = 1000):
		"""
			Zadawanie zapytania do poliqarpd.

			@param query 	- zapytanie w postaci tekstowej
			@param bufsize	- maksymalna ilość odpowiedzi (ograniczenie poliqarpd)

			@returns lista obiektów PoliqarpDaemonClient.Answer
		"""
		assert (type(bufsize) is IntType) and (type(query) is StringType)

		if not self.__command("MAKE-QUERY " + query):
			print "Query \'%s\' is not valid." % query
			return []

		self.__command("BUFFER-RESIZE %d" % bufsize)

		res = self.__command("RUN-QUERY %d" % bufsize, 1)

		occurences = int(res[0][2])

		if not occurences:
			return []

		output 	= []
		begin	= 0
		end		= 10

		while begin < occurences:
			if end >= occurences:
				end = occurences - 1

			res = self.__command("GET-RESULTS %d %d" % (begin, end))

			res = [ res[i][1] for i in range(len(res)) ]

			for i in range(end - begin + 1):
				# lewy kontekst
				n_lctx	= int(res.pop(0))
				lctx 	= res[0 : n_lctx]

				del res[0: n_lctx]

				# segmenty
				assert int(res.pop(0)) == 0

				n_segs	= int(res.pop(0))
				segs	= []

				# dla każdego segmentu
				for s in range(n_segs):
					orth 		= res.pop(0)
					baseforms 	= []
					
					# ilość niejednoznacznych otagowań
					n_tags = int(res.pop(0))

					# pobierz pary (forma bazowa, tagi)
					for t in range(n_tags):
						baseforms.append((res.pop(0), res.pop(0)))

					# dopisz kolejny segment
					segs.append(PoliqarpWord(orth, baseforms))

				# prawy kontekst
				n_rctx	= int(res.pop(0))
				rctx 	= res[0 : n_rctx]
				
				del res[0: n_rctx]

				# dodaj wynik do listy
				output.append(PoliqarpDaemonClient.Answer(lctx, segs, rctx))

			begin	+= 10
			end		+= 10

		return output

	class Answer:
		"""
			Klasa przechowująca informację o pojedyńczym wyniku zapytania do
			serwera poliqarpd. Implementuje iterator i operator indeksowania
			po wszystkich segmentach.

			@field lctx	- lista słów kontekstu po lewej stronie segmentów
			@field rctx	- lista słów kontekstu po prawej stronie segmentów
		"""

		def __init__(self, lctx, segs, rctx):
			self.__lctx = lctx
			self.__segs = segs
			self.__rctx = rctx

			self.__iter_index = 0
		
		def __getattr__(self, name):
			if name == "lctx":
				return self.__lctx
			elif name == "rctx":
				return self.__rctx
			else:
				raise AttributeError(name)

		def __len__(self):
			return len(self.__segs)

		def __getitem__(self, key):
			if (type(key) is not IntType) or (key < 0) or (key >= len(self)):
				raise IndexError

			return self.__segs[key]

		def __iter__(self):
			self.__iter_index = 0
			return self

		def next(self):
			if self.__iter_index == len(self):
				raise StopIteration

			r = self[self.__iter_index] 

			self.__iter_index += 1

			return r


