import asyncio
import discord
import logging
import random

client = discord.Client()
class Player:
	def __init__(self, discord_u, game):
		self.discord_user = discord_u
		self.name = discord_u.name
		self.new_dm_command = None
		self.parent_game = game
		self.log = logging.getLogger("game."+game.name+"."+self.name)

	async def assign_role(self, role, hitler, fascists):
		self.party = role
		await self.send("You are " + self.party + "!")
		if role == "Liberal":
			await self.send("Kill Hitler, elect 5 liberal policies, and crush those fascists")
		elif role == "Fascist":
			await self.send("Your Hitler is " + hitler + ", and you fascist(s) are " + " ".join(fascists))
		elif role == "Hitler":
			await self.send("Fascists know your true identity, but those dirty so-called 'liberals' don't! \
			Manipulate them into electing you as a chancellor to take over political scene!")
		elif role == "Socialist":
			await self.send("Commit working revolution!")

	async def send(self, message):
		try:
			await self.discord_user.create_dm()
		except:
			pass
		self.log.info("Got message: " + message)
		if len(message)>0:
			await self.discord_user.dm_channel.send(message)
		else:
			self.log.warning("Tried to send empty message!")


	async def input(self, processing, private_only, *messages):
		while True:
			if len(messages)>0:
				await self.send("\n".join(messages))
			
			while True:
				self.last_message = None
				while self.last_message == None:
					await asyncio.sleep(0.25)
				self.log.info("Recieved a message: " + self.last_message.content)
				if self.last_message.content.startswith("$"):
					if not private_only or self.last_message.channel == self.discord_user.dm_channel:
						self.last_message.content = self.last_message.content[1:]
						if processing(self.last_message) != None:
							await self.send("Thanks for your vote!")
							return processing(self.last_message)


	def check(self):
		return self.new_dm_command!=None

	def playerparse(self, cmd):
		try:
			if len(cmd.mentions) == 1:
				for p in self.parent_game.players:
					if cmd.mentions[0] == p.discord_user:
						return p
			elif int(cmd.content) <= len(self.parent_game.players):
				return self.parent_game.players[int(cmd.content)-1]
		except:
			return None
	def lawparse(self, cmd):
		try:
			if int(cmd.content) <= 3:
				return int(cmd.content)-1
		except:
			return None
	def voteparse(self, cmd):
		try:
			if cmd.content.lower() in ["ja", "yes", "true"]:
				return True
			elif cmd.content.lower() in ["nein", "no", "false"]:
				return False
		except:
			return None




class Game:
	def __init__(self, name, game_channel):
		self.name = name
		self.log = logging.getLogger("game." + name)
		self.public_channel = game_channel
		self.setupped = False
		self.running = False
		self.players = []

	

	async def play(self, balans = None, override = False):
		#setup
		#self.players = list_of_players
		

		self.override = override
		end = None

		self.veto = False
		self.hitler_can_overtake = False

		self.failed_governments = 0
		self.presindex = 0

		self.president = None
		self.chancellor = None
		self.chairman = None

		if balans == None:
			balans = "b" + str(len(self.players))
		if len(balans) == 1:
			balans += len(self.players)
		if not self.setupped:
			if not self.setup_settings(balans):
				self.log.error("Setupping settings by balance code failed")
				await self.public_channel.send("Setupping settings by balance code failed")
				return False

		self.draw_deck = []
		self.discard_deck = []
		for key in self.deck_contents:
			self.draw_deck+=([key for _ in range(self.deck_contents[key])])
		random.shuffle(self.draw_deck)
		random.shuffle(self.players)
		fascists = [self.players[i+1].name for i in range(self.roles.count("Fascist"))]
		self.log.info("Assigning roles")
		for i in range(len(self.players)):
			await self.players[i].assign_role(self.roles[i], self.players[0].name, fascists)
		random.shuffle(self.players)
		self.running = True

		#actual game
		self.log.info("Starting an actual game")
		while end == None:
			await self.shuffle()
			await self.give_info()
			if await self.elect_government():
				await self.policy_playing()
		await self.public_channel.send("Its " + end)
		self.log.info("END, reason: " + end)
		return end
		

	def setup_settings(self, balance): #string balance
		if len(balance) == 0 or len(balance)>3:
			self.log.error("Got wrong balance code")
			return False
		if len(balance) == 1:
			players = len(self.players)
		else:
			players = int("".join(balance[1:]))
		
		if balance[0] == 's':
			if players < 6:
				self.log.error("Less than 6 players in socialist edition")
				return False
			self.roles = None
			self.parties_playing = ["Liberal", "Fascist", "Socialist"]
			self.chairman_allowed = True
			self.deck_contents = {
				"Liberal": 5,
				"Fascist": 10,
				"Socialist": 8
			}
			self.board_format = {
				"Liberal": [[None], [None], [None], [None]],
				"Fascist": [[None], [self.investigate], [self.special_election, self.allow_hitler_overtake], [self.shoot], [self.shoot, self.allow_veto]],
				"Socialist": [[None], [self.recruitment], [self.five_year_plan, self.censorship], [self.recruitment]]
			}
			self.board = {
				"Liberal":  0,
				"Fascist":  0,
				"Socialist": 0
			}
			self.roles = ["Hitler"] + ["Fascist"]*((players-2)//3) + ["Socialist"]*((players-1)//4) + ["Liberal"]*(players//2)
			if players == 7:
				self.roles.append("Liberal")

			if players >= 9:
				self.board_format["Socialist"].append([self.confession])
			if players <= 10:
				self.board_format["Socialist"][0] = [self.bugging]
				self.board_format["Socialist"][3] = [self.congress]
		else:
			if players < 5:
				self.log.error("Less than 5 players in game")
				return False
			self.roles = None
			self.chairman_allowed = False
			self.parties_playing = ["Liberal", "Fascist"]
			self.deck_contents = {
				"Liberal": 6,
				"Fascist": 11,
			}
			self.board_format = { #at the end is always party victory
				"Liberal":  [[None], [None], [None], [None]],
				"Fascist":  [[None], [self.investigate], [self.special_election, self.allow_hitler_overtake], [self.shoot], [self.shoot, self.allow_veto]],
			}
			self.board = {
				"Liberal":  0,
				"Fascist":  0,
			}
			self.roles = ["Hitler"] + ["Fascist"]*((players-3)//2) + ["Liberal"]*(players//2 + 1)

		self.setupped = True
		self.log.info("Setupped settings by balance code " + balance)
		return True

	'''
	def setup_settings(self, balans):
		self.parties_playing = ["Liberal", "Fascist"]
		self.deck_contents = {
			"Liberal": 6, 
			"Fascist": 11,
			#"Socialist": 0
			}
		self.board_format = { #at the end is always party victory
			"Liberal":  [[None], [None], [None], [None]],
			"Fascist":  [[None], [self.investigate], [self.special_election, self.allow_hitler_overtake], [self.shoot], [self.shoot, self.allow_veto]],
			#"Socialist":[]
			}
		self.board = {
			"Liberal":  0,
			"Fascist":  0,
			#"Socialist":0
			}
		self.roles_playing = [None, 
						None, 
						None, 
						None, 
						[["Hitler", "Fascist", "Liberal", "Liberal", "Liberal"]], 
						[["Hitler", "Fascist", "Liberal", "Liberal", "Liberal", "Liberal"]],
						[["Hitler", "Fascist", "Fascist", "Liberal", "Liberal", "Liberal", "Liberal"]],
						[["Hitler", "Fascist", "Fascist", "Liberal", "Liberal", "Liberal", "Liberal", "Liberal"]],
						[["Hitler", "Fascist", "Fascist", "Fascist", "Liberal", "Liberal", "Liberal", "Liberal", "Liberal"]],
						[["Hitler", "Fascist", "Fascist", "Fascist", "Liberal", "Liberal", "Liberal", "Liberal", "Liberal", "Liberal"]],
						
						]

		self.log.info("Finished setupping game settings")

	'''
	async def add_fail(self):
		self.failed_governments+=1
		self.log.info("One more failed government")
		if self.failed_governments:
			self.log.info("Topdeck")
			await self.public_channel.send("3 Governments failed, it is a TOPDECK")
			await self.chosen_policy(self.draw_deck[0])
			self.draw_deck.pop(0)


	async def shuffle(self):
		if len(self.draw_deck)<3:
			self.log.info("Shuffling deck")
			self.draw_deck+=self.discard_deck
			random.shuffle[self.draw_deck]
			self.discard_deck = []


	async def elect_government(self, advance_president = True):
		if advance_president:
			self.presindex = (self.presindex+1)%len(self.players)
			self.president = self.players[self.presindex]
		while True:
			chosen_chancellor = await self.president.input(self.president.playerparse, False, "Choose your chancellor, by number or by mention")
			if chosen_chancellor != self.president and chosen_chancellor!=self.chancellor:
				break
			self.log.warning("Invalid chancellor chosen")
			if self.override:
				self.log.debug("Bad input overriden")
				break
		

		await self.send_everyone("Vote Ja! or Nein! for goverment, where " + self.president.name + " is president, and " + chosen_chancellor.name + " is chancellor.", "Your vote:")
		
		self.log.info("Gathering votes...")
		votes = await asyncio.gather(*[p.input(p.voteparse, True) for p in self.players])

		#results
		#votectionary = {}
		printstring = ""
		for ind, v in enumerate(votes):
			if v:
				votes[ind] = "<:ja:618529433703415869>"
			else:
				votes[ind] = "<:nein:618529433678118931>"
			#votectionary[self.players[ind]] = v
			printstring += str(ind+1) + ". " + self.players[ind].name + ": " + votes[ind] +"\n"
		self.log.info(printstring)
		await self.public_channel.send(printstring)

		if votes.count("<:ja:618529433703415869>") > votes.count("<:nein:618529433678118931>"):
			await self.public_channel.send("This government passed! President is " + self.president.name + " and chancellor is " + chosen_chancellor.name)
			self.log.info("Government passed")
			if chosen_chancellor.party == "Hitler" and self.hitler_can_overtake:
				end = "Hitler became chancellor!"
				return
			self.chancellor = chosen_chancellor
			self.failed_governments = 0
			if self.chairman_allowed:
				msg = await public_channel.send(chancellor.name + " is now choosing chairman...")
				chosen = await self.chancellor.input(chancellor.playerparse, False, "Choose your chairman!")
				if chosen != self.president and chosen != self.chancellor:
					self.chairman = chosen
					await self.public_channel.send(self.chairman.name + " is now chairman!")
					await msg.edit(content = chancellor.name + " has chosen " + self.chairman.name + " as chairman!")
			return True

		else: 
			await self.add_fail()
		return False

	async def player_join(self, player):
		if not self.running:
			self.players.append(Player(player, self))
			self.log.info("Player " + player.name + " joined")
			return True
		return False

	async def player_leave(self, player):
		for u in self.players:
			if u.discord_user == player:
				self.log.info("Player " + u.name + " left")
				await self.public_channel.send("Player " + u.name + " left")
				self.players.remove(u)
				return True
		self.log.error(player.name + " is not in this game, so he can't leave")
		await self.public_channel.send("You cannot leave game you are not in")
		return False
				

	async def send_everyone(self, public_message, private):
		self.log.info("Public channel output: " + public_message)
		await self.public_channel.send(public_message)
		for p in self.players:
			await p.send(private)

	def new_message(self, message):
		for p in self.players:
			if message.author == p.discord_user:
				self.log.debug("Sending last recieved command for '" + p.name + "' to: " + message.content)
				p.last_message = message

	async def chosen_policy(self, policy):
		self.board[policy]+=1
		track = self.board_format[policy]
		await self.public_channel.send(policy + " policy comes into play!")
		self.log.info(policy + " was elected")
		if len(track) == self.board[policy]:
			self.end = policy + " victory by laws!"
			return
		if track[self.board[policy]-1][0] != None:
			for action in track[self.board[policy]-1]:
				await action()

	async def policy_playing(self):
		hand = self.draw_deck[:3]
		self.draw_deck = self.draw_deck[3:]
		hand.sort()
		if self.chairman_allowed:
			seen = random.choice(hand)
			self.log.info("Chairman saw " + seen + " policy")
			await self.chairman.send("One of presidents policies is also " + seen + " policy.")
			await self.public_channel.send("Chairman saw one policy! President should be rather careful about discarding policies...")
		msg = await self.public_channel.send("President is discarding a policy. . .")
		number = await self.president.input(self.president.lawparse, True, "Discard one policy by typing number: " + " ".join(hand))
		self.discard_deck.append(hand[number])
		hand.pop(number)


		await msg.edit(content = "President discarded a policy, waiting for chancellor. . .")
		number = 2
		if self.veto:
			while number > 1:
				number = self.chancellor.input(self.chancellor.lawparse, True, "Discard one policy by typing number or VETO to initiate veto  "  + " ".join(hand))
				if number.lower() == "veto":
					self.log.info("VETO initiated by chancellor")
					await self.public_channel.send("Chancellor wants to VETO. . .")
					if self.president.input(self.president.voteparse, True, "Do you agree with VETO?"):
						self.log.info("VETO succesfull")
						await self.public_channel.send("All policies are discarded. This government is considered failed.")
						await self.add_fail()
					else:
						self.log.info("VETO refused by president")

		while number > 1:
			number = await self.chancellor.input(self.chancellor.lawparse, True, "Discard one policy by typing number: " + " ".join(hand))

		await msg.edit(content = "President discarded a policy, chancellor did so too")
		self.discard_deck.append(hand[number])
		hand.pop(number)
		
		await self.chosen_policy(hand[0])
		
	async def investigate(self):
		inved = await self.president.input(self.president.playerparse, False, "Choose one player to investigate")
		self.log.info("President investigating " + inved.name)
		answer = inved.party
		if answer == "Hitler": answer = "Fascist"
		await self.president.send(inved.name + " is " + answer)
		msg = await self.public_channel.send(president.name+" investigated " + inved.name + ". We are now waiting for his claim. . .")
		
		claim = 5
		while claim > len(self.parties_playing):
			claim = await self.president.input(self.president.lawparse, False, "Do you want to tell, that " + inved.name + " is. . .\n" \
											" ,".join(self.parties_playing))
		claim = self.parties_playing[claim-1]
		await msg.edit(content = president.name+" investigated " + inved.name + ". He claims, that he is a " + claim)
		self.log.info("Claims " + claim)

	async def shoot(self):
		self.log.info("Shootin...")
		await self.public_channel.send()
		shot = await self.president.input(president.playerparse, False, "Choose one player to shoot")
		self.log.info("President shot " + shot.name)
		
		if shot.party=="Hitler":
			self.end = "Hitler killed"
			return
		self.players.remove(shot)


	async def allow_veto(self):
		self.log.info("VETO allowed")
		self.veto = True

	async def allow_hitler_overtake(self):
		self.hitler_can_overtake = True


	async def special_election(self):
		self.log.info("Special election")
		lastpres = self.president
		while True:
			SEpres = await self.president.input(self.president.playerparse, False, "Choose your SPECIAL president, by number or by mention")
			if SEpres != self.president:
				break
		self.president = SEpres
		await self.shuffle()
		if await self.elect_government(advance_president = False):
			await self.policy_playing()
		self.president = lastpres

	async def recruitment(self):
		self.log.info("Socialist recruiting...")

		msg = await self.public_channel.send("Socialist is recruiting someone. Wait for him...")
		socs = []
		for p in self.players:
			if p.party == "Socialist":
				socs.append(p)
		
		recruiter = random.choice(socs)
		recruited = await recruiter.input(recruiter.playerparse, True, "Hey, socialist. You are chosen to recruit one of other players to join socialist party!. Type number of player with dollar before.")
		self.log.info(recruiter.name + " is recruiting " + recruited.name)
		if recruited.party != "Hitler":
			await recruited.send("Hey! Abandon your nooby teammates, and join Socialist REVOLUTION!! (You are now playing as socialist)")
		else:
			await recruited.send("Lol. Some stoopid socialist just tried to convince you, that socialism is better than fascism. But you know what is right! (You stay fascist, because you are Hitler)")
			self.log.info("Hitler cannot be recruited. Nobody is recruited")

		for s in socs:
			await s.send(recruiter.name + " recruited " + recruited.name)
		await msg.edit(content = "Socialist is recruiting someone. Done! Who can you trust now..?")
		

	async def five_year_plan(self):
		self.log.info("Five year plan")
		await self.public_channel.send("2 Socialist and 1 Liberal policy are now shuffled into deck. ")
		self.draw_deck += ["Socialist", "Socialist", "Liberal"]
		random.shuffle(self.draw_deck)

	async def censorship(self):
		self.log.info("Censorship")
		self.chairman_allowed = False
		self.chairman = None
		await self.public_channel.send("Chairman is now wiped out of existence. Say goodbye or press F")

	async def bugging(self):
		self.log.info("Socialist bugging...")

		msg = await self.public_channel.send("Socialist is bugging someone. Wait for him...")
		socs = []
		for p in self.players:
			if p.party == "Socialist":
				socs.append(p)
		
		bugger = random.choice(socs)
		bugged = await bugger.input(bugger.playerparse, True, "Hey, socialist. You are chosen to bug one of other players. Type number of player with dollar before.")
		self.log.info(bugger.name + " bugged " + bugged.name)
		seen_party = bugged.party
		if seen_party == "Hitler":
			seen_party = "Fascist"
		for s in socs:
			await s.send(bugger.name + " bugged " + bugged.name + ". He is " + seen_party)

	async def congress(self):
		self.log.info("Congress")
		socs = []
		for p in self.players:
			if p.party == "Socialist":
				socs.append(p)


		for s in socs:
			await s.send("Socialistic congress! Several people came. Those people were (including you): " + ", ".join(socs))

	async def confession(self):
		self.log.info("Confession")
		conf_player = await self.president.input(self.president.playerparse, False, "Choose one player to confess to")
		self.log.info("President has confessed to " + conf_player.name)
		answer = self.president.party
		if answer == "Hitler": answer = "Fascist"
		await self.conf_player.send(self.president.name + " is " + answer)
		msg = await self.public_channel.send(president.name+" has confessed to " + conf_player.name + ". We are now waiting for his claim. . .")
		
		claim = 5
		while claim > len(self.parties_playing):
			claim = await conf_player.input(conf_player.lawparse, False, "Do you want to tell, that " + self.president.name + " is. . .\n" \
											" ,".join(self.parties_playing))
		claim = self.parties_playing[claim-1]
		await msg.edit(content = president.name+" has confessed to " + conf_player.name + ". He claims, that he is a " + claim)
		self.log.info("Claims " + claim)

	async def give_info(self, channel = None):
		if channel == None:
			channel = self.public_channel

		printstring = ""
		if self.running	:
			if self.president != None:
				printstring = "President is now " + str(self.president.name)
			if self.chancellor != None:
				printstring += "\nChancellor was " + str(self.chancellor.name)
			if self.chairman != None and self.chairman_allowed:
				printstring += "\nChairman was " + str(self.chairman.name)

			printstring += "\nPolicies are:\n"
			for p in self.board:
				printstring += p + " policies: " + str(self.board[p]) + "\n"
			for p in range(len(self.players)):
				printstring += str(p+1) + ": " + self.players[p].name + "\n"
			#for p in self.board_format:
			#	printstring += p + "\n"
		else:
			printstring += "Players in this game are:\n"
			for p in self.players:
				printstring += p.name + "\n"
			if self.setupped:
				printstring += "Game is setupped by code\n"
			else:
				printstring += "Game is not setupped by code. Default settings will take place\n"
			printstring += "Owner of this game is " + self.players[0].name + "\n"

		await channel.send(printstring)




@client.event
async def on_ready():
	global hra
	gamelog = logging.getLogger('game')
	hra = Game("TEST", client.get_channel(578267016700493844))
	server = client.get_guild(570211422315872256)
	userplayerids = [332935845004705793, 578266009576669187, 386518852994990101, 316969123407986689, 528160997614157874]
	#for i in userplayerids:
	#	hra.player_join(client.get_user(i))
	#for i in range()
	await hra.setup_settings("s10") 
	print("Hey, setupdone")

@client.event
async def on_message(message):
	global hra
	if message.content.lower() == "$info":
		await hra.give_info(channel = message.channel)
	if message.author != client.get_guild(570211422315872256).me:
		hra.new_message(message)


if __name__ == "__main__":
	logscope = logging.INFO 
	logging.basicConfig(level=logscope)




	client.run('NTY3NjgxMDk5NjMxNjg5NzI4.XOAvVw.40gqM8sF2p8e39xYXoyYlsE7k-U')
