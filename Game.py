import pygame, sys, random, time, threading, pygame_menu, keyboard #must be installed: pip install keyboard in anaconda cmd
from Table import Table
from Animations import Animations
from Button import Button
from pygame.locals import *
from pygame import mixer
from Score import Score
from Player import Player
from Teams import Team
from random import randint
from pathlib import Path
from Fireworks import Firework, update
from BoxColor import BoxColor

running = True
cursorStrings = (
    "                ",
    "XXXXXX          ",
    "XXXXXX          ",
    "XX....XX        ",
    "XX....XX        ",
    "XX......XX      ",
    "XX......XX      ",
    "  XX......XX    ",
    "  XX......XX    ",
    "    XX......XX  ",
    "    XX......XX  ",
    "      XX..XXXX  ",
    "      XX..XXXX  ",
    "        XXXX    ",
    "        XXXX    ",
    "                ")

cursor = pygame.cursors.compile(cursorStrings, black='X', white='.', xor='o')

class Game():
    def __init__(self):
        #multiplayer-----------#eventually will be read from File; some variables still need to be saved by the functions in multiplayerOptions
        self.streakToOneUp = 3 #streak until a oneUp is given
        self.roundsToComplete = 3 #number of decks completed until game complete
        self.teamCount = 0 #how many teams
        self.playerCount = 2  #how many players
        self.tempPlayerCnt = 0 #in order to properly reset the game if wanted
        self.playersInTeams = [0,0,0,0,0,0,0] #if there is a team with 0 players, then that team does not exist according to the user
        self.livesPerTeams = [0,0,0,0,0,0,0]
        self.lives = 2 #how many lives per team; may add switch to select lives per player or lives per team
        self.showIntroSequence=True #whetehr cards are shown at the beginnging of the game
        self.introSequenceTime=3 #how long the cards are displayed at the beginning of the game
        self.FFA = True #if there are 0 teams
        self.co_op = False #if there is 1 team
        self.error = False #set to true when there is any user error; this will not let the user exit the menu until they fix the error
        self.timeBetweenTurns = 1 #time between turns for players
        self.col = 3 #how many columns in the multiplayer table
        self.row = 3 #how many rows in the multiplayer table
        self.randomOrder = False
        self.turnIter = 0 #The number which marks how many of the players have already played before going back to the first activeplayer
        
        #for variables which should not be saved after exiting the menu; a little messy, I know
        self.tmpTeamCnt = self.teamCount
        self.tmpCoop = self.co_op
        self.tmpFFA = self.FFA
        self.tmpPlayersInTeam = self.playersInTeams
        self.tmpPlyCnt = self.playerCount
        self.tmpShIntSeq = self.showIntroSequence
        self.tmpIntSeq = self.introSequenceTime
        self.tmpTimeBT = self.timeBetweenTurns
        self.tmpLives = self.lives
        self.tmpStreakToOneUp = self.streakToOneUp
        self.tmpRandOrder = self.randomOrder
       
        #singlePlayer-----------
        self.difficulty = int(self.readSettingFromFile("SavedVariables.txt", "difficulty"))
        self.gamemode = int(self.readSettingFromFile("SavedVariables.txt", "gamemode"))
        #both----------
        self.flipTime = 2 #
        self.volume = int(self.readSettingFromFile("SavedVariables.txt", "volume"))
        self.selectedTheme = self.readCardTheme()
        self.FPS = int(self.readSettingFromFile("SavedVariables.txt", "FPS"))
        self.screenWidth = int(self.readSettingFromFile("SavedVariables.txt", "screenWidth"))
        self.screenHeight = int(self.readSettingFromFile("SavedVariables.txt", "screenHeight"))
        self.fullscreen = int(self.readSettingFromFile("SavedVariables.txt", "fullscreen"))
        self.mainClock = pygame.time.Clock()
        self.animate = Animations(self.FPS)
        self.green = (0, 255, 0)
        self.red = (255, 0, 0)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.buttonFont = pygame.font.SysFont('Times New Roman', 20)
        self.lifeFont = pygame.font.SysFont('Times New Roman', 20)
        self.endFont = pygame.font.SysFont('Times New Roman', 32)
        self.boxColor = BoxColor()
    def draw_text(self, text, font, color, x, y, window):
        img = font.render(text, True, color)
        textRect = img.get_rect()
        textRect.topleft = (x, y)
        window.blit(img, textRect)

    def draw_text_center(self, text, font, color, x, y, window):
        img = font.render(text, True, color)
        textRect = img.get_rect()
        textRect.center = (x, y)
        window.blit(img, textRect)
        
    #sets the scale of the cards depending on both the resolution and number of cards, available space, and the space between cacrds; 
    #output is a float which is the amount to scale the cards by
    def setCardScale(self, minBorder, cols, rows, inBTween):
        screenWidth = self.screenWidth - minBorder * 2
        screenHeight = self.screenHeight - minBorder * 2
        dim = 0

        if (cols * 5 / screenWidth > rows * 7 / screenHeight):  # or cols < rows + 2):
            xLength = screenWidth / cols - inBTween
            dim = xLength / 250
        else:
            yLength = screenHeight / rows - inBTween
            dim = yLength / 350
        return dim
    
    #reads a setting froma  file based on file name and file variable name. Assumes that file is set up as "varName=val"
    #ouputs "val"
    def readSettingFromFile(self, fName, sName):
        file = open(fName, 'r')
        string = None
        for line in file:
            if (line.startswith(sName)):
                string = line
                break
        string = string.replace(sName + "=", "")
        string = string.replace("\n", "")
        file.close()
        return string
    
    #saves a setting to a file based on file name and file variable name. Assumes that file is set up as "varName=val"
    #save "newVal" to "varName"
    def saveSettingToFile(self, fName, sName, sValue):
        file = open(fName, "r")
        settings = []
        for line in file:
            if (line.startswith(sName)):
                oldVal = line.replace(sName + "=", "")
                line = line.replace(oldVal, sValue)
            if (line != "\n"):
                settings.append(line)
        file.close()
        print(settings)
        file = open(fName, "w")
        for setting in settings:
            file.write(setting + "\n")
        file.close()
        
    #uses the readFile to pick the card theme
    def readCardTheme(self):
        InitialCardSetting = self.readSettingFromFile("SavedVariables.txt", "selectedTheme")
        InitialCardSetting = InitialCardSetting.replace("theme_", "")
        print(InitialCardSetting)
        return InitialCardSetting
    
    #uses saveFile to save the card theme
    def saveInitialCardTheme(self, newTheme):
        self.selectedTheme = newTheme
        newTheme = "theme_" + newTheme
        self.saveSettingToFile("SavedVariables.txt", "selectedTheme", newTheme)
        
    #an inbetween menu which allows the user to choose multiplayer or singleplayer  
    def sOrMOptions(self, screen):
        self.screen = screen
        textSize = 20
        while True:
            screen.fill((202, 228, 241))
            
            MENU_MOUSE_POS = pygame.mouse.get_pos()
            
            # Single Player Game Button
            sp_button = Button(image=pygame.image.load("Assets/LargerButtonBG.jpg"), pos=(self.screenWidth*1/4, self.screenHeight*4/8), 
                            text_input="Single Player", font=pygame.font.Font("assets/font.ttf", textSize), base_color="#d7fcd4", hovering_color="White")

            # Single Player Options Button
            sp_options_button = Button(image=pygame.image.load("Assets/ButtonBG.jpg"), pos=(self.screenWidth*1/4, self.screenHeight*6/8), 
                            text_input="Options", font=pygame.font.Font("assets/font.ttf", textSize), base_color="#d7fcd4", hovering_color="White")
            
            # Multi Player Game Button
            mp_button = Button(image=pygame.image.load("Assets/LargerButtonBG.jpg"), pos=(self.screenWidth*3/4, self.screenHeight*4/8), 
                           text_input="Multi Player", font=pygame.font.Font("assets/font.ttf", textSize), base_color="#d7fcd4", hovering_color="White")

            # Multi Player Options Button
            mp_options_button = Button(image=pygame.image.load("Assets/ButtonBG.jpg"), pos=(self.screenWidth*3/4, self.screenHeight*6/8), 
                           text_input="Options", font=pygame.font.Font("assets/font.ttf", textSize), base_color="#d7fcd4", hovering_color="White")
            
            # Back Button to return to Main Menu
            back_button = Button(image=pygame.image.load("Assets/LargerButtonBG.jpg"), pos=(self.screenWidth*2/4, self.screenHeight*2/8), 
                           text_input="Back to Main Menu", font=pygame.font.Font("assets/font.ttf", textSize), base_color="#d7fcd4", hovering_color="White")
            
            #Initialize buttons on to the screen and allow mouse interaction
            for button in [sp_button, sp_options_button, mp_button, mp_options_button, back_button]:
                button.changeColor(MENU_MOUSE_POS)
                button.update(screen)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mixer.init()
                        mixer.music.load('Sounds/mainmenu.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Button events when specific buttons are clicked
                    if sp_button.checkForInput(MENU_MOUSE_POS):
                        self.game(screen)

                    if sp_options_button.checkForInput(MENU_MOUSE_POS):
                        self.singlePlayerOptions(screen)
                
                    if mp_button.checkForInput(MENU_MOUSE_POS):
                        self.multiPlayerGame(screen)

                    if mp_options_button.checkForInput(MENU_MOUSE_POS):
                        self.multiplayerOptions(screen)
            
                    if back_button.checkForInput(MENU_MOUSE_POS): 
                        mixer.init()
                        mixer.music.load('Sounds/mainmenu.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        return
            
            pygame.display.update()
            self.mainClock.tick(self.FPS)
            
    #the options of the single player mode
    def singlePlayerOptions(self, screen):
       optionsMenu = screen
       goBackButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, self.screenHeight /6), "Go Back:", self.buttonFont, "White", "#d7fcd4")
       menuTheme = pygame_menu.themes.Theme(
           background_color=(202, 228, 241),
           title_background_color=(0, 0, 0, 0),
       )

       menu = pygame_menu.Menu(
           title="",
           height=self.screenHeight/2,
           width=self.screenWidth,
           theme=menuTheme)
       
       livesOn = int(self.gamemode) & 0x01
       timeOn = (int(self.gamemode) & 0x02) >> 1
       
       #based off a switch, sets global lives on or off
       def setLivesOption(isLives, **kwargs):
           if(isLives):
               self.gamemode |= 0x1
           else:
               self.gamemode &= 0xE
           self.saveSettingToFile('SavedVariables.txt', 'gamemode', str(self.gamemode))
           print(livesOn, " ", timeOn, " ", self.gamemode)

       #based off a switch, set global time on or off
       def setTimeOption(isTime, **kwargs):
           if(isTime):
               self.gamemode |= 0x2
           else:
               self.gamemode &= 0xD
           self.saveSettingToFile('SavedVariables.txt', 'gamemode', str(self.gamemode))
           print(livesOn, " ", timeOn, " ", self.gamemode)
       livesSwitch = menu.add.toggle_switch("Lives", onchange=setLivesOption, default=livesOn)
       timeSwitch = menu.add.toggle_switch("Timer", onchange=setTimeOption, default=timeOn)
       
       #sets the difficulty as easy, medium or hard
       def setDifficulty(difficulty, difficultyIndex, **kwargs):
           value_tuple, index = difficulty
           self.difficulty = value_tuple[1]
           self.saveSettingToFile("SavedVariables.txt", "difficulty", str(value_tuple[1]))
       allDifficulties = [('Easy', 0),
                         ('Medium', 1),
                         ('Hard', 2)]
       difficultySelector = menu.add.dropselect(
           title="Difficulty",
           items=allDifficulties,
           # placeholder=allThemes[defaultCardTheme][0],
           onchange=setDifficulty,
           scrollbar_thick=5,
           selection_option_font=self.lifeFont,
           # selection_box_border_color=(0,0,0,0),
           selection_box_width=250,
           selection_box_height=250,
           placeholder= allDifficulties[self.difficulty][0],
           placeholder_add_to_selection_box=False
       )
       
       livesSwitch.add_self_to_kwargs()
       timeSwitch.add_self_to_kwargs()
       difficultySelector.add_self_to_kwargs()  # Callbacks will receive widget as parameter
       
       # running = True
       while True:
           optionsMenu.fill((202, 228, 241))
           mouse = pygame.mouse.get_pos()
           for button in [goBackButton]:
               button.changeColor(mouse)
               button.update(optionsMenu)
           pygame_menu.widgets.core.widget.pygame.mouse.set_cursor((16, 16), (0, 0), *cursor)
           
           events = pygame.event.get()
           # events2 = pygame.event.get()
           menu.draw(optionsMenu)
           menu.update(events)
           for event in events:
               if event.type == pygame.MOUSEBUTTONDOWN:
                   if goBackButton.checkForInput(mouse):
                       return
               if event.type == pygame.KEYDOWN:
                   if event.key == pygame.K_ESCAPE:
                       mixer.init()
                       mixer.music.load('Sounds/mainmenu.mp3')
                       mixer.music.set_volume(self.volume/100)
                       mixer.music.play(-1)
                       return
           pygame.display.update()
           self.mainClock.tick(self.FPS)
    
    #options for the multiplayer mode
    def multiplayerOptions(self, screen):
        from pygame_menu.locals import INPUT_FLOAT, INPUT_INT, INPUT_TEXT #allows float, ints, texts to be used as an input type for text boxes
        
        optionsMenu = screen
        menuTheme = pygame_menu.themes.Theme(
            background_color=(202, 228, 241),
            title_background_color=(0, 0, 0, 0),
        )
        
        goBackButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2-170, self.screenHeight /8), "Go Back:", self.buttonFont, "White", "#d7fcd4")
        finishedButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2+170, self.screenHeight /8), "Finished:", self.buttonFont, "White", "#d7fcd4")

        menu = pygame_menu.Menu(
            title="",
            height=(self.screenHeight - 200),
            position = (self.screenWidth/2 - 350, self.screenHeight /8 + 100, False),
            width=700,
            center_content = False,
            theme=menuTheme)
        
        #reveals the number of teams based off the number of teams chosen; 
        """need to change so that the values are only saved once there is no user error"""
        #sets the number of teams and sets whehter global FFA and co_op should be true or false.
        def setTeamsOption(teamCountStr, teamCnt, **kwargs):
            self.tmpTeamCnt = teamCnt
            #print(self.teamCount)
            if(teamCnt <= 1):
                errorPlayerCountLable.hide()
                self.error = False
                if(teamCnt):
                    self.tmpCoop = True
                    self.tmpFFA = False
                else:
                    self.tmpFFA = True
                    self.tmpCoop = False
                for team in range(maxTeamsEver):
                    teamPlayerCountSelectors[team].hide()
                    self.tmpPlayersInTeam[team] = 0
                return
            else:
                self.tmpFFA = False
                self.tmpCoop = False
                
            for team in range(teamCnt):
                teamPlayerCountSelectors[team].show()
                self.tmpPlayersInTeam[team] = teamPlayerCountSelectors[team].get_value()[1]
            for team in range(maxTeamsEver - teamCnt):
                #print(-1 * (team - maxTeamsEver) - 1)
                teamPlayerCountSelectors[-1 * (team - maxTeamsEver) - 1].hide()
                self.tmpPlayersInTeam[-1 * (team - maxTeamsEver) - 1] = 0
                
            #print("-------------------")W

            if(teamCnt > 1):
                checkPlayerCountPerTeamOptions(None, None)
                
        #sets the number of total players
        def setPlayerCountOptions(playerCountStr, playerCnt, **kwargs):
            #print(teamCount)
            teamCountList.clear()
            for players in range(playerCnt):
                stringPC = None
                stringPC = str(players)
                intPC = players
                teamCountList.append((stringPC, intPC))
            #print(playerCnt <= self.teamCount)
            if playerCnt <= self.tmpTeamCnt:
                #print(playerCnt)
                teamSelector.set_value(str(playerCnt-1))
                setTeamsOption(None, playerCnt-1)
            teamSelector.update_items(teamCountList)
            self.tmpPlyCnt = playerCnt
            checkPlayerCountPerTeamOptions(None, None)
        
        #both sets the number of players per team and checks that they equal the number of total players
        def checkPlayerCountPerTeamOptions(playerCountStr, playerCnt, **kwargs):
            attemptedPlayerCnt = 0
            for team in teamPlayerCountSelectors:
                if int(team.get_id()) > self.tmpTeamCnt - 1:
                    break
                self.tmpPlayersInTeam[int(team.get_id())] = team.get_value()[1] + 1
                #print(team.get_id())
                #print(team.get_value()[1] + 1)
                attemptedPlayerCnt += team.get_value()[1] + 1
                #print(attemptedPlayerCnt)
                #print(self.playerCount)
            if not errorPlayerCountLable.is_visible() and attemptedPlayerCnt != self.tmpPlyCnt and self.tmpTeamCnt >= 2:
                self.error = True
                errorPlayerCountLable.show()
            elif errorPlayerCountLable.is_visible() and attemptedPlayerCnt == self.tmpPlyCnt:
                self.error = False
                errorPlayerCountLable.hide()
                
        #reveals the text box for the time for the intro sequence if the introSequenceSwitch is set to showing
        def setIntroSequence(isPlay, **kwargs):
            self.tmpShIntSeq = isPlay
            if(isPlay):
                introSequenceTimeText.show()
            else:
                introSequenceTimeText.hide()
                
        #sets the time for the intro sequence        
        def setIntroSequenceTime(time, **kwargs):
            self.tmpIntSeq = time
        
        #sets the time between turns
        def setTimeBetweenTurns(time, **kwargs):
            self.tmpTimeBT = time
            
        #sets the lives
        def setLives(lives, **kwargs):
            if(lives == 0): lives += 1
            elif(lives > 1000): lives = 1000
            self.tmpLives = abs(lives)
            
        def setStreakToOneUp(streakToOneUp, **kwargs):
            if(streakToOneUp == 0): streakToOneUp += 1
            self.tmpStreakToOneUp = abs(streakToOneUp)
        
        maxTeamsEver = 7 #since there are only allowed 8 possible players (because I think it would be too many after that), then there are only 7 possible teams. Otherwise it is a free for all, or complete co-op
        
        #needed: ability to select saved game modes - drop selection
        
        #There probably should be a way to delete modes too, but that would be hard I think
        
        introSequenceSwitch = menu.add.toggle_switch("Intro Sequence", onchange=setIntroSequence, state_text=("Skip", "Play"), default=self.showIntroSequence, align=pygame_menu.locals.ALIGN_LEFT)
        introSequenceTimeText = menu.add.text_input("In seconds, show Cards for: ", default=self.introSequenceTime, onchange=setIntroSequenceTime, input_type=INPUT_FLOAT, align=pygame_menu.locals.ALIGN_RIGHT)
        
        def setXCards(strX, x, **kwargs):
            self.col = x
        
        def setYCards(strY, y, **kwargs):
            self.row = y
        
        def setRandomOrder(isRand, **kwargs):
            self.tmpRandOrder = isRand
        
        numCards = [("3", 3), ("4", 4), ("5", 5)]
        
        xSelector = menu.add.selector("Cards x dimension",
                                      items=numCards,
                                      onchange=setXCards,
                                      style=pygame_menu.widgets.SELECTOR_STYLE_FANCY,
                                      align=pygame_menu.locals.ALIGN_LEFT
                                      )
        
        ySelector = menu.add.selector("Cards y dimension",
                                      items=numCards,
                                      onchange=setYCards,
                                      style=pygame_menu.widgets.SELECTOR_STYLE_FANCY,
                                      align=pygame_menu.locals.ALIGN_LEFT
                                      )
        
        livesPerTextBox = menu.add.text_input("Lives: ", default=self.lives, onchange=setLives, input_type=INPUT_INT, align=pygame_menu.locals.ALIGN_LEFT)
        streakPerTextBox = menu.add.text_input("streak to one-up: ", default=self.streakToOneUp, onchange=setLives, input_type=INPUT_INT, align=pygame_menu.locals.ALIGN_LEFT)
        
        playerCountList = [("2", 2),("3", 3),("4", 4),("5", 5),("6", 6),("7", 7), ("8", 8)]
        playerCountSelector = menu.add.selector("Total Player Count", 
                                                items=playerCountList, 
                                                onchange=setPlayerCountOptions, 
                                                style=pygame_menu.widgets.SELECTOR_STYLE_FANCY, 
                                                align=pygame_menu.locals.ALIGN_LEFT
                                                )
        
        teamCountList = []

        for players in range(self.playerCount):
            stringPC = None
            stringPC = str(players)
            intPC = players
            teamCountList.append((stringPC, intPC))
        teamSelector = menu.add.selector("Teams", items=teamCountList, onchange=setTeamsOption, style=pygame_menu.widgets.SELECTOR_STYLE_FANCY, align=pygame_menu.locals.ALIGN_LEFT)
        teamPlayerCountList = [("1", 1),("2", 2),("3", 3),("4", 4),("5", 5),("6", 6),("7", 7)]
        teamPlayerCountSelectors = [] #the number of players per team
        xSelector.set_default_value(self.col)
        ySelector.set_default_value(self.row)
        playerCountSelector.set_default_value(self.playerCount - 2) #this ensures that the default value is correct; if the default in the parameters, it crashes.
        playerCountSelector.reset_value()
        teamSelector.set_default_value(self.teamCount) #this ensures that the default value is correct; if the default in the parameters, it crashes.
        teamSelector.reset_value()
        for i in range(maxTeamsEver):
            teamName = "Team " + str(i + 1) + " size"
            teamCountSelector = menu.add.selector(
                 teamName, 
                 selector_id=str(i),
                 items=teamPlayerCountList, 
                 onchange=checkPlayerCountPerTeamOptions, 
                 style=pygame_menu.widgets.SELECTOR_STYLE_FANCY, 
                 align=pygame_menu.locals.ALIGN_RIGHT
             )
            teamPlayerCountSelectors.append(teamCountSelector)
        
        errorPlayerCountLable = menu.add.label("The Added Player Count of Individual Teams needs to match the Total Player Count", font_size=10, align=pygame_menu.locals.ALIGN_LEFT)
        
        timeBetweenTurnsText = menu.add.text_input("In seconds, time between turns: ", default=self.timeBetweenTurns, onchange=setTimeBetweenTurns, input_type=INPUT_FLOAT, align=pygame_menu.locals.ALIGN_LEFT)
        
        randomOrderSwitch = menu.add.toggle_switch("Random Turn Order", onchange=setRandomOrder, state_text=("Off", "On"), default=self.randomOrder, align=pygame_menu.locals.ALIGN_LEFT)
        
        randomOrderSwitch.add_self_to_kwargs()
        streakPerTextBox.add_self_to_kwargs()
        livesPerTextBox.add_self_to_kwargs()
        introSequenceTimeText.add_self_to_kwargs()
        introSequenceSwitch.add_self_to_kwargs()
        if(not self.tmpShIntSeq):
            introSequenceTimeText.hide()
        #else:introSequenceTimeText.show()
        timeBetweenTurnsText.add_self_to_kwargs()
        playerCountSelector.add_self_to_kwargs()
        xSelector.add_self_to_kwargs()
        ySelector.add_self_to_kwargs()
        teamSelector.add_self_to_kwargs()
        for team in range(maxTeamsEver):
            teamPlayerCountSelectors[team].add_self_to_kwargs()
        if(self.tmpTeamCnt > 1):
            for team in range(maxTeamsEver - self.tmpTeamCnt):
                #print(-1 * (teams - maxTeams) - 1) 
                teamPlayerCountSelectors[-1 * (team - maxTeamsEver) - 1].hide()
        else:
            for team in range(maxTeamsEver):
                #print(-1 * (teams - maxTeams) - 1) 
                teamPlayerCountSelectors[-1 * (team - maxTeamsEver) - 1].hide()
        errorPlayerCountLable.add_self_to_kwargs()
        errorPlayerCountLable.hide()
        
        checkPlayerCountPerTeamOptions(None, None)
        #tmp vars are used so that if there is an error, it will not be saved; this method reverts the tmp vars to working variables upon exiting if there are errors
        def revertTmpVars():
            self.tmpTimeBT = self.timeBetweenTurns
            self.tmpIntSeq = self.introSequenceTime
            self.tmpShIntSeq = self.showIntroSequence
            self.tmpPlyCnt = self.playerCount
            self.tmpTeamCnt = self.teamCount
            self.tmpCoop = self.co_op
            self.tmpFFA = self.FFA
            self.tmpPlayersInTeam = self.playersInTeams
            self.tmpLives = self.lives
            self.tmpStreakToOneUp = self.streakToOneUp
            self.tmpRandOrder = self.randomOrder
            self.error = False
            
        #tmp vars are used so that if there is an error, it will not be saved; this method saves the tmp vars to the vars used in the multiplayer game variables upon exiting if there are error
        def applyTmpVars():
            self.timeBetweenTurns = self.tmpTimeBT 
            self.introSequenceTime = self.tmpIntSeq
            self.showIntroSequence = self.tmpShIntSeq
            self.playerCount = self.tmpPlyCnt
            self.teamCount = self.tmpTeamCnt
            self.co_op = self.tmpCoop
            self.FFA = self.tmpFFA
            self.playersInTeams = self.tmpPlayersInTeam
            self.lives = self.tmpLives
            self.streakToOneUp = self.tmpStreakToOneUp
            self.randomOrder = self.tmpRandOrder


            
        while True:
            #print(self.playersInTeams)
            optionsMenu.fill((202, 228, 241))
            mouse = pygame.mouse.get_pos()
            pygame_menu.widgets.core.widget.pygame.mouse.set_cursor((16, 16), (0, 0), *cursor)
            
            for button in [goBackButton, finishedButton]:
                button.changeColor(mouse)
                button.update(optionsMenu)
            self.draw_text_center("values not saved", self.buttonFont, self.white, self.screenWidth/2-170, self.screenHeight /8 + 20, optionsMenu)
            self.draw_text_center("Values Saved if no errors", self.buttonFont, self.white, self.screenWidth/2+170, self.screenHeight /8 + 20, optionsMenu)
            events = pygame.event.get()
            # events2 = pygame.event.get()
            menu.draw(optionsMenu)
            menu.update(events)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    print(self.error)
                    if goBackButton.checkForInput(mouse):
                        pygame.mixer.music.stop()
                        revertTmpVars()
                        return
                        #window.fill(self.black)
                        #return [False, False, True]
                    elif finishedButton.checkForInput(mouse) and self.error == False:
                        pygame.mixer.music.stop()
                        applyTmpVars()
                        return
                        #self.showScores(window, str(score))
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.mixer.music.stop()
                        revertTmpVars()
                        return
            pygame.display.update()
            self.mainClock.tick(self.FPS)
    
    #sets the settings of the game: resolution; theme; FPS; volume; fullscreen
    def settingsOptions(self, screen):

        optionsMenu = screen
        menuTheme = pygame_menu.themes.Theme(
            background_color=(202, 228, 241),
            title_background_color=(202, 228, 241),
        )
        goBackButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, self.screenHeight /6), "Go Back:", self.buttonFont, "White", "#d7fcd4")

        menu = pygame_menu.Menu(
            title="",
            height=self.screenHeight/2,
            width=self.screenWidth,
            theme=menuTheme)
        
        #chooses the card theme to be saved and used
        def setCardTheme(newThemeName, newThemeNameButLike___Again, **kwargs):
            # global selectedTheme
            value_tuple, index = newThemeName
            # selectedTheme = value_tuple[0]
            self.saveInitialCardTheme(value_tuple[0])

        allCardThemes = [('Tarot', 'Tarot'),
                         ('Pokemon', 'Pokemon'),
                         ('Mario', 'Mario'),
                         ('Poker', 'Poker'),
                         ('Final Fantasy 14', 'Final Fantasy 14'),
                         ('NFL', 'NFL'),
                         ('Developer', 'Developer')]
        themeSelector = menu.add.dropselect(
            title="Deck Theme",
            items=allCardThemes,
            # placeholder=allThemes[defaultCardTheme][0],
            onchange=setCardTheme,
            scrollbar_thick=5,
            selection_option_font=self.lifeFont,
            # selection_box_border_color=(0,0,0,0),
            selection_box_width=250,
            selection_box_height=250,
            placeholder=self.selectedTheme,
            placeholder_add_to_selection_box=False
        )
        
        #saves the resolution values to be used
        def setResolution(newRes, resX, resY, **kwargs):
            global screen
            value_tuple, index = newRes
            self.screenWidth = resX
            self.screenHeight = resY
            if self.fullscreen:
                screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), pygame.FULLSCREEN)
                #self.saveSettingToFile("SavedVariables.txt", "fullscreen", str(True))
            else:
                screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), 0, 32)
            menu.resize(resX, resY)
            self.saveSettingToFile("SavedVariables.txt", "screenWidth", str(resX))
            self.saveSettingToFile("SavedVariables.txt", "screenHeight", str(resY))

        allResolutions = [('2560 x 1440', 2560, 1440),
                          ('1920 x 1080', 1920, 1080),
                          ('1600 x 900', 1600, 900),
                          ('1280 x 720', 1280, 720)]
        resolutionSelector = menu.add.dropselect(
            title="Resolution",
            items=allResolutions,
            # placeholder=allThemes[defaultCardTheme][0],
            onchange=setResolution,
            scrollbar_thick=5,
            selection_option_font=self.lifeFont,
            # selection_box_border_color=(0,0,0,0),
            selection_box_width=250,
            selection_box_height=250,
            placeholder= str(self.screenWidth) + " x " + str(self.screenHeight),
            placeholder_add_to_selection_box=False
        )

        #sets the volume value to be used
        def set_vol(range, **kwargs):
            val = int(range)
            self.volume = int(val)
            mixer.music.set_volume(self.volume/100)
            self.saveSettingToFile("SavedVariables.txt", "volume", str(val))
            #set volume of mixer takes value only from 0 to 1, val is divided by 100

        volumeSlider = menu.add.range_slider(
            title="Volume",
            default=self.volume,
            range_values=(0, 100),
            increment=1,
            onchange = set_vol,
            value_format=lambda x: str(int(x)),
           # command = set_vol()
        )
        
        #decides whether fullscreen is being used or not
        def fullscreen(isFullscreen, **kwargs):
            global screen
            self.fullscreen = isFullscreen
            if self.fullscreen:
                screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), pygame.FULLSCREEN)
                self.saveSettingToFile("SavedVariables.txt", "fullscreen", str(1))
            else:
                screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), 0, 32)
                self.saveSettingToFile("SavedVariables.txt", "fullscreen", str(0))

        
        fullscreenToggle = menu.add.toggle_switch("Fullscreen", onchange = fullscreen, default=self.fullscreen)
        
        themeSelector.add_self_to_kwargs()  
        resolutionSelector.add_self_to_kwargs()  
        volumeSlider.add_self_to_kwargs()
        fullscreenToggle.add_self_to_kwargs()

        # running = True
        while True:
            optionsMenu.fill((202, 228, 241))
            mouse = pygame.mouse.get_pos()
            for button in [goBackButton]:
                button.changeColor(mouse)
                button.update(optionsMenu)
            pygame_menu.widgets.core.widget.pygame.mouse.set_cursor((16, 16), (0, 0), *cursor)
            events = pygame.event.get()
            # events2 = pygame.event.get()
            menu.draw(optionsMenu)
            menu.update(events)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if goBackButton.checkForInput(mouse):
                        mixer.init()
                        mixer.music.load('Sounds/mainmenu.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mixer.init()
                        mixer.music.load('Sounds/mainmenu.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        return
            pygame.display.update()
            self.mainClock.tick(self.FPS)

    def main_menu(self):
        print("fullscreen" + str(self.fullscreen))
        if self.fullscreen:
            screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((self.screenWidth, self.screenHeight), 0, 32)

        titleFont = pygame.font.Font("assets/font.ttf", 50)

        # Main Menu Music
        mixer.init()
        mixer.music.load('Sounds/mainmenu.mp3')
        mixer.music.set_volume(self.volume/100)
        mixer.music.play(-1)
        
 
        pygame.mouse.set_cursor((16, 16), (0, 0), *cursor)
        
        
        white = (255, 255, 255)
        black = (0, 0, 0)

        
        while True:       
            screen.fill((202, 228, 241))
            self.draw_text_center('Memory Matching', titleFont, white,  self.screenWidth / 2, self.screenHeight / 6, screen)
            self.draw_text_center('Game', titleFont, white,  self.screenWidth / 2, self.screenHeight / 4, screen)

            MENU_MOUSE_POS = pygame.mouse.get_pos()

            # Start Game Button
            START_BUTTON = Button(image=pygame.image.load("Assets/ButtonBG.jpg"), pos=(self.screenWidth/2, self.screenHeight*3/8), 
                            text_input="Start Game", font=pygame.font.Font("assets/font.ttf", 25), base_color="#d7fcd4", hovering_color="White")

            # Options buttons
            OPTIONS_BUTTON = Button(image=pygame.image.load("Assets/ButtonBG.jpg"), pos=(self.screenWidth/2, self.screenHeight*5/8), 
                            text_input="Options", font=pygame.font.Font("assets/font.ttf", 25), base_color="#d7fcd4", hovering_color="White")

            # Quit Game Button
            QUIT_BUTTON = Button(image=pygame.image.load("Assets/ButtonBG.jpg"), pos=(self.screenWidth/2, self.screenHeight*7/8), 
                            text_input="Quit", font=pygame.font.Font("assets/font.ttf", 25), base_color="#d7fcd4", hovering_color="White")

            #Initialize buttons on to the screen and allow mouse interaction
            for button in [START_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
                button.changeColor(MENU_MOUSE_POS)
                button.update(screen)
        
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mixer.init()
                        mixer.music.load('Sounds/mainmenu.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Button events when specific buttons are clicked
                    if START_BUTTON.checkForInput(MENU_MOUSE_POS):
                        self.chooseBoxColor()
                        mixer.init()
                        mixer.music.load('Sounds/loading.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play()
                        screen.fill(self.boxColor.getCol())
                        self.sOrMOptions(screen)

                    if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                        mixer.init()
                        mixer.music.load('Sounds/settings.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play(-1)
                        self.settingsOptions(screen)
                    
                    if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                        pygame.quit()
                        sys.exit()
            
            pygame.display.update()
            self.mainClock.tick(self.FPS)
            
    def centerDeckX(self, xSize, col, screenWidth, minBorder):
        deckX = xSize * col
        availableSpace = screenWidth - minBorder * 2
        toXCenter = availableSpace - deckX
        toXCenter /= 2
        return toXCenter
    #same as sleep, but allows for parallel processes
    def stopAllFor(self, seconds):
        global running
        startTime = time.perf_counter()
        timeSinceStart = 0
        while timeSinceStart <= seconds and running:
            timeSinceStart = time.perf_counter()
            timeSinceStart -= startTime
            time.sleep(0.05)
        pygame.event.clear()
    
    def chooseBoxColor(self):
        savedVariablesFile = open("SavedVariables.txt", "r")
        selTheme = savedVariablesFile.read()
        developerTheme = "selectedTheme=theme_Developer"
        if(developerTheme in selTheme):
            self.boxColor.setCol(0, 0, 0)
            self.animate.boxColor.x = 0
            self.animate.boxColor.y = 0
            self.animate.boxColor.z = 0
        mariotheme = "selectedTheme=theme_Mario"
        if (mariotheme in selTheme):
            self.boxColor.setCol(255, 0, 0)
            self.animate.boxColor.x = 255
            self.animate.boxColor.y = 0
            self.animate.boxColor.z = 0
        tarottheme = "selectedTheme=theme_Tarot"
        if (tarottheme in selTheme):
            self.boxColor.setCol(22, 26, 43)
            self.animate.boxColor.x = 22
            self.animate.boxColor.y = 26
            self.animate.boxColor.z = 43
        pokemontheme = "selectedTheme=theme_Pokemon"
        if (pokemontheme in selTheme):
            self.boxColor.setCol(0, 160, 255)
            self.animate.boxColor.x = 0
            self.animate.boxColor.y = 160
            self.animate.boxColor.z = 255
        pokertheme = "selectedTheme=theme_Poker"
        if (pokertheme in selTheme):
            self.boxColor.setCol(100, 100, 100)
            self.animate.boxColor.x = 255
            self.animate.boxColor.y = 0
            self.animate.boxColor.z = 0
        ffxivtheme = "selectedTheme=theme_Final Fantasy 14"
        if (ffxivtheme in selTheme):
            self.boxColor.setCol(50, 0, 100)
            self.animate.boxColor.x = 210
            self.animate.boxColor.y = 180
            self.animate.boxColor.z = 140
        nfltheme = "selectedTheme=theme_NFL"
        if (nfltheme in selTheme):
            self.boxColor.setCol(0, 150, 0)
            self.animate.boxColor.x = 0
            self.animate.boxColor.y = 150
            self.animate.boxColor.z = 0

        
        
    #while this will be very similar to the game method, it's different enough I feel to where a new method is warrented. 
    def multiPlayerGame(self, window):
        #print(self.FFA)   
        print("randomOrder: ", self.randomOrder)
        players = []
        playerOrder = []
        if(self.FFA):
            self.tempPlayerCnt = self.playerCount
        elif(not (self.co_op)):
            self.tempPlayerCnt = self.teamCount
        for i in range(self.playerCount):
            player = Player(i + 1, self.lives, -1)
            players.append(player)
            players[i].ID = i + 1
            playerOrder.append(player)
            playerOrder[i].ID = i + 1
        if(self.randomOrder):
            random.shuffle(playerOrder)
        for i in playerOrder:
            print(i.ID)

        if(self.co_op):
            self.tempPlayerCnt = 2 #this really should be one, but the game crashes if it's 1 so...
            self.playersInTeams[0] = self.playerCount

        teamsData = []
        teamNum = 0
        cnt = 0
        for i in self.playersInTeams:
            #print(i)
            if i == 0:
                break
            for j in range(i):
                print("cnt: " + str(cnt+j))
                players[cnt + j].teamNum = teamNum
                print("team: " + str(teamNum))
            cnt += i
            team = Team(teamNum, self.lives)
            teamNum+=1
            teamsData.append(team)    
        #allows escape to be used at almost anytime
        def parallelEscape():
            global running
            while True:
                if keyboard.is_pressed("Esc"):
                    #when exiting game this will play main menu sound in the select screen, not finished
                    mixer.init()
                    mixer.music.load('Sounds/mainmenu.mp3')
                    mixer.music.set_volume(self.volume/100)
                    mixer.music.play(-1)
                    running = False
                time.sleep(0.05)
        
                
        global running
        running = True
        
        es = threading.Thread(target=parallelEscape)
        es.start()
        #window.fill(self.black)
        
        bg = pygame.image.load("images/theme_Developer/defaultbg.jpg")
        
        savedVariablesFile = open("SavedVariables.txt", "r")
        selTheme = savedVariablesFile.read()
        mariotheme = "selectedTheme=theme_Mario"
        if (mariotheme in selTheme):
            bg = pygame.image.load("images/theme_Mario/mariowallpaper.jpg")
        tarottheme = "selectedTheme=theme_Tarot"
        if (tarottheme in selTheme):
            bg = pygame.image.load("images/theme_Tarot/tarotwallpaper.jpg")
        pokemontheme = "selectedTheme=theme_Pokemon"
        if (pokemontheme in selTheme):
            bg = pygame.image.load("images/theme_Pokemon/pokemonwallpaper.jpg")
        pokertheme = "selectedTheme=theme_Poker"
        if (pokertheme in selTheme):
            bg = pygame.image.load("images/theme_Poker/pokerwallpaper.jpg")
        ffxivtheme = "selectedTheme=theme_Final Fantasy 14"
        if (ffxivtheme in selTheme):
            bg = pygame.image.load("images/theme_Final Fantasy 14/ffxivwallpaper.jpg")
        nfltheme = "selectedTheme=theme_NFL"
        if (nfltheme in selTheme):
            bg = pygame.image.load("images/theme_NFL/nflwallpaper.jpg")
        
        
        bg = pygame.transform.scale(bg, (self.screenWidth, self.screenHeight))
        window.blit(bg, (0,0))
        
        t = Table(self.col, self.row, self.selectedTheme, 5, 0, self.FPS)

        green = (0, 255, 0)
        red = (255, 0, 0)
        white = (255, 255, 255)
        black = (0, 0, 0)
        
        playerMinBorder = 40
        minBorder = 120
        inBTween = 5
        scale = self.setCardScale(minBorder, t.x, t.y, inBTween)
        xDim = int(250 * scale)
        yDim = int(350 * scale)
        xSize = xDim + inBTween
        ySize = yDim + inBTween
        toXCenter = self.centerDeckX(xSize, t.x, self.screenWidth, minBorder)
        timeToFlip = int(3000 * scale)  # can't be too fast or frames don't register
        
        path_to_background_music_file = 'Sounds/'+str(self.selectedTheme)+'.mp3'
        background_music_path = Path(path_to_background_music_file)
        
        mixer.init()
        if background_music_path.is_file():
            mixer.music.load('Sounds/'+str(self.selectedTheme)+'.mp3')
        else: 
            mixer.music.load('Sounds/Mario.mp3')
        mixer.music.set_volume(self.volume/100)
        mixer.music.play(-1)
        
        tempTable = []
        

        def livesVisualUpdate(players):
            squareH = 40
            squareX = 40
            print("FFA: " + str(self.FFA))
            if(self.FFA):
                for i in range(self.playerCount):
                    squareY = (i * 80) + playerMinBorder
                    lives = players[i].lives
                    if(lives == 0):
                        lives = "--"
                    textYLoc = (squareY + squareH/2) + 40
                    window.fill(self.boxColor.getCol(), (squareX, textYLoc, 150, 15))  
                    self.draw_text("lives:" + str(lives),  pygame.font.Font("assets/font.ttf", 15), self.white, squareX, textYLoc, window)
            elif(not (self.FFA)):
                cnt = 0
                teamNum = 0
                for i in self.playersInTeams:
                    if i == 0:
                        break
                    cnt += i
                    squareY = ((cnt - 1) * 80) + playerMinBorder
                    lives = teamsData[teamNum].lives
                    print(str(teamNum) + " has " + str(lives) + " lives")
                    teamNum += 1
                    if(lives == 0):
                        lives = "--"
                    textYLoc = (squareY + squareH/2) + 40
                    window.fill(self.boxColor.getCol(), (squareX, textYLoc, 150, 15))  
                    self.draw_text("lives:" + str(lives),  pygame.font.Font("assets/font.ttf", 15), self.white, squareX, textYLoc, window)
        def turnFrame(players):
            squareH = 40
            squareX = 40
            for i in range(self.playerCount):
                squareY = (i * 80) + playerMinBorder
                textYLoc = (squareY + squareH/2) + 25
                window.fill(self.boxColor.getCol(), (squareX + 50, textYLoc - 40, 30, 30))
        turnFrame(players)
                
        def streakVisualUpdate(players):
            squareH = 40
            squareX = 40
            if(self.FFA):
                for i in range(self.playerCount):
                    squareY = (i * 80) + playerMinBorder
                    streak = players[i].streak
                    textYLoc = (squareY + squareH/2) + 25
                    window.fill(self.boxColor.getCol(), (squareX, textYLoc, 150, 15))
                    self.draw_text("streak:" + str(streak),  pygame.font.Font("assets/font.ttf", 15), self.white, squareX, textYLoc, window)
                #pygame.display.update()
            elif(not (self.FFA)):
                cnt = 0
                teamNum = 0
                for i in self.playersInTeams:
                    #print(i)
                    if i == 0:
                        break
                    cnt += i
                    squareY = ((cnt-1) * 80) + playerMinBorder
                    streak = teamsData[teamNum].streak
                    teamNum += 1
                    textYLoc = (squareY + squareH/2) + 25
                    window.fill(self.boxColor.getCol(), (squareX, textYLoc, 150, 15))  
                    self.draw_text("streak:" + str(streak),  pygame.font.Font("assets/font.ttf", 15), self.white, squareX, textYLoc, window)
        #visually indicates who's turn it is    
        def activePlayerVisualUpdate(activePlayer, prevActivePlayer):
            print(str(activePlayer + 1))
            squareH = 10
            squareX = 100
            squareY = (activePlayer * 80) + playerMinBorder + 15
            prevSquareY = (prevActivePlayer * 80) + playerMinBorder + 15
            window.fill(self.boxColor.getCol(), (squareX, prevSquareY , squareH, squareH))
            activeSquare = pygame.Rect(squareX, squareY, squareH, squareH)
            
            colX, colY, colZ = self.boxColor.getCol()
            colX = 255 - colX
            colY = 255 - colY
            colZ = 255 - colZ
            
            pygame.draw.rect(window, (colX,colY,colZ), activeSquare)
            #pygame.display.update()
        #sets up the players team colors, lives, and streak
        def setUpMPTable(players):
            def getTeamColor(team):
                if team == 0:
                    return (255, 0, 0)
                elif team == 1:
                    return (0, 255, 0)
                elif team == 2:
                    return (0, 0, 255)
                elif team == 3:
                    return (255, 255, 0)
                elif team == 4:
                    return (0, 255, 255)
                elif team == 5:
                    return (255, 0, 255)
                elif team == 6:
                    return (127, 127, 127)
                else:
                    return (255, 255, 255)
                
            #sets up card display
            tempTable.clear()
            for i in range(t.x):
                for j in range(t.y):
                    t.table[j][i].col = i
                    t.table[j][i].row = j
                    tempTable.append(t.table[j][i])
                    surface = t.table[j][i].image.convert()
                    surface = pygame.transform.scale(surface, (xDim, yDim))
                    window.blit(surface, ((minBorder + toXCenter) + xSize * t.table[j][i].col, minBorder + ySize * t.table[j][i].row))
            #sets up players display
            squareX = 40
            squareW = 40
            squareH = 40
            for i in range(self.playerCount):
                #image=pygame.image.load("Assets/ButtonBG.jpg")
                squareY = (i * 80) + playerMinBorder
                
                playerDisplay = pygame.Surface((squareW, squareH))
                playerDisplay.fill(getTeamColor(players[i].teamNum))
                window.blit(playerDisplay, (squareX, squareY))
                
                player = "P" + str(players[i].ID)
                textXLoc = (squareX + squareW/2)
                textYLoc = (squareY + squareH/2)
                self.draw_text_center(player, pygame.font.Font("assets/font.ttf", 15), self.black, textXLoc, textYLoc, window)
            streakVisualUpdate(players)
            livesVisualUpdate(players)
            pygame.display.update()
            
            if(self.showIntroSequence):
                self.stopAllFor(0.5)
                self.animate.flip(tempTable, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                self.stopAllFor(self.introSequenceTime)
                if(not running):
                    pygame.event.clear()
                    return False
                self.animate.flip(tempTable, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                
        window.fill(self.boxColor.getCol(), (self.screenWidth/2 - 70, self.screenHeight/12 - 10, 140, 18))
        roundsComplete = 0
        self.draw_text_center("round: " + str(roundsComplete + 1), pygame.font.Font("assets/font.ttf", 15), self.white, self.screenWidth/2, self.screenHeight/12, window)
        setUpMPTable(players)
        activePlayerVisualUpdate(playerOrder[0].ID - 1, playerOrder[0].ID - 1)
        
        #finds the next player who's turn it is; skips not alive players
        def findNextAlivePlayer(players, activePlayer):
            livesVisualUpdate(players)
            streakVisualUpdate(players)
            prevActivePlayer = activePlayer
            self.stopAllFor(self.timeBetweenTurns)
            if(self.co_op and self.tempPlayerCnt <= 1):
                return activePlayer
            while True:
                print("playerCount", str(self.playerCount))
                print("turnIter ", self.turnIter)
                if(self.turnIter == self.playerCount):
                    self.turnIter = -1
                    random.shuffle(playerOrder)
                print("ID ", playerOrder[self.turnIter].ID)
                activePlayer = playerOrder[self.turnIter].ID - 1
                self.turnIter +=1
                if(players[activePlayer].alive == True):
                    if(not self.FFA and teamsData[players[activePlayer].teamNum].alive == False):
                        continue
                break
            activePlayerVisualUpdate(activePlayer, prevActivePlayer)
            
            return activePlayer
        
        #either marks the player as not alive if they have 1 life or subtracts a life
        def playerIsOutOrRemoveLife(players, activePlayer):
            if(self.FFA):
                players[activePlayer].lives -= 1
                if (players[activePlayer].lives == 0):
                    players[activePlayer].alive = False
                    self.tempPlayerCnt -= 1
                else:
                    players[activePlayer].streak = 0
            elif(not (self.FFA)):
                teamEffected = players[activePlayer].teamNum
                print("teamEffected " + str(teamEffected))
                teamsData[teamEffected].lives -= 1
                if (teamsData[teamEffected].lives == 0):
                    teamsData[teamEffected].alive = False
                    self.tempPlayerCnt -= 1
                else:
                    teamsData[teamEffected].streak = 0
            activePlayer = findNextAlivePlayer(players, activePlayer)
            return activePlayer
        def winOrLoseMusicAndScreen():
            win = False
            if(self.co_op):
                if gameover_path.is_file():
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+' Gameover.mp3')
                else: 
                    mixer.music.load('Sounds/Mario Gameover.mp3')
            else:
                if victory_path.is_file():
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+' Victory.mp3')
                else: 
                    mixer.music.load('Sounds/Mario Victory.mp3')
                win = True
            return win
            
            mixer.music.set_volume(self.volume/120)
            mixer.music.play()
        #if a player has a streak of 3, a new life is added. The next active player is then found
        def playerGetsOneUpOrNextTurn(players, activePlayer):
            if(self.FFA):
                players[activePlayer].streak += 1
                if(players[activePlayer].streak == self.streakToOneUp):
                    players[activePlayer].lives += 1
                    players[activePlayer].streak = 0
            elif(not (self.FFA)):
                teamEffected = players[activePlayer].teamNum
                teamsData[teamEffected].streak += 1
                if(teamsData[teamEffected].streak == self.streakToOneUp):
                    teamsData[teamEffected].lives += 1
                    teamsData[teamEffected].streak = 0
            activePlayer = findNextAlivePlayer(players, activePlayer)
            return activePlayer
        activePlayer = playerOrder[0].ID - 1
        self.turnIter = 0
        self.turnIter += 1  
        path_to_victory_file = 'Sounds/'+str(self.selectedTheme)+' Victory.mp3'
        path_to_gameover_file = 'Sounds/'+str(self.selectedTheme)+' Gameover.mp3'
        victory_path = Path(path_to_victory_file)
        gameover_path = Path(path_to_gameover_file)
        #findNextAlivePlayer(players, activePlayer)
        while running:
            self.mainClock.tick(self.FPS)

            mouse = pygame.mouse.get_pos()
 
            #here, rather than checking for a win, this checks for a completed deck
            if t.checkWin():
                activePlayer = playerGetsOneUpOrNextTurn(players, activePlayer)
                for i in tempTable:
                    if not i.shown:
                        card = [i]
                        self.animate.flip(card, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                        self.stopAllFor(0.2)
                        break
                self.animate.flip(tempTable, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                t = Table(self.col, self.row, self.selectedTheme, 5, 0, self.FPS)
                window.fill(self.boxColor.getCol(), (self.screenWidth/2 - 70, self.screenHeight/12 - 10, 140, 18))
                roundsComplete += 1 
                self.draw_text_center("round: " + str(roundsComplete + 1), pygame.font.Font("assets/font.ttf", 15), self.white, self.screenWidth/2, self.screenHeight/12, window)
                setUpMPTable(players)
            else:
                t.update()
                for i in range(t.x):
                    for j in range(t.y):
                        surface = t.table[j][i].image.convert()
                        surface = pygame.transform.smoothscale(surface, (xDim, yDim))
                        t.table[j][i].rect = surface.get_rect()
                        t.table[j][i].makeRect((minBorder + toXCenter) + xSize * i, minBorder + ySize * j)
                pygame.display.update()
                
                if len(t.selection) >= 1:
                    if t.checkBomb():
                        self.stopAllFor(1)
                        for c in t.selection:
                            if not (c.ID == "BOMB"):
                                cards = []
                                cards.append(c)
                                self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                        
                        t.selection.clear()
                        activePlayer = playerIsOutOrRemoveLife(players, activePlayer)
                        if(self.tempPlayerCnt <= 1):
                            hidenCards = []
                            for i in tempTable:
                                if not i.shown:
                                    hidenCards.append(i)
                            self.animate.flip(hidenCards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                            win = winOrLoseMusicAndScreen()
                            mixer.music.set_volume(self.volume/120)
                            mixer.music.play()
                            self.stopAllFor(3.0)
                            running, playAgain = self.endScreen(window, t.score, False, win)

                    if len(t.selection) >= 2:
                        isMatch = t.checkMatch()
                        #bomb
                        if isMatch == 2:
                            self.stopAllFor(1)
                            if(running):
                                self.animate.flip(t.selection, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                                t.selection.clear()
                                activePlayer = playerIsOutOrRemoveLife(players, activePlayer)
                                if(self.tempPlayerCnt <= 1):
                                    hidenCards = []
                                    for i in tempTable:
                                        if not i.shown:
                                            hidenCards.append(i)
                                    self.animate.flip(hidenCards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                                    win = winOrLoseMusicAndScreen()
                                    mixer.music.set_volume(self.volume/120)
                                    mixer.music.play()
                                    self.stopAllFor(3.0)
                                    running, playAgain = self.endScreen(window, t.score, False, win)

                        else:
                            if isMatch == 1:
                                match = t.selection[1].ID if t.selection[1].ID != "JOKER" else t.selection[0].ID
                                t.selection.clear()
                                for r in t.table:
                                    for c in r:
                                        if c.ID == match and not c.shown:
                                            cards = []
                                            cards.append(c)
                                            self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                            t.selection.clear()
                            activePlayer = playerGetsOneUpOrNextTurn(players, activePlayer)

                for row in t.table:
                    for c in row:
                        if (c.rect.collidepoint(mouse) and not c.shown):
                            for event in pygame.event.get():
                                if event.type == pygame.MOUSEBUTTONDOWN:
                                    cards = [c]
                                    self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window,
                                                      True)

                                    t.selection.append(c)
                                    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  
            
        es.join(0)
        return
        
    def game(self, window):
        def updateLivesStreakTimeScoreVisual(t, textCol, timeLeft, window):
            #window.fill(self.boxColor, (0, 0, 400, 40))  # so cards show during lose screen
            window.fill(self.boxColor.getCol(), (0, 0, self.screenWidth, 40))  # so cards show during lose screen
            if self.gamemode == 1:
                self.draw_text("Lives: " + str(t.lives), self.lifeFont, textCol, 5, 0, window)
            elif self.gamemode == 2:
                self.draw_text("Time: " + str(timeLeft) + "s", self.lifeFont, textCol, 5, 0, window)
            elif self.gamemode == 3:
                self.draw_text("Lives: " + str(t.lives), self.lifeFont, textCol, 5, 0, window)
                self.draw_text("Time: " + str(timeLeft) + "s", self.lifeFont, textCol, 5, 20, window)

            self.draw_text("Score: " + str(t.score), self.lifeFont, textCol, 105, 0, window)
            
        def parallelEscape():
            global running
            while True:
                if keyboard.is_pressed("Esc"):
                    #when exiting game this will play main menu sound in the select screen, not finished
                    mixer.init()
                    mixer.music.load('Sounds/mainmenu.mp3')
                    mixer.music.set_volume(self.volume/100)
                    mixer.music.play(-1)
                    running = False
                time.sleep(0.05)
                
        global running
        running = True
        
        es = threading.Thread(target=parallelEscape)
        es.start()
        #window.fill(self.black)
        
        bg = pygame.image.load("images/theme_Developer/defaultbg.jpg")
        
        savedVariablesFile = open("SavedVariables.txt", "r")
        selTheme = savedVariablesFile.read()
        mariotheme = "selectedTheme=theme_Mario"
        if (mariotheme in selTheme):
            bg = pygame.image.load("images/theme_Mario/mariowallpaper.jpg")
        tarottheme = "selectedTheme=theme_Tarot"
        if (tarottheme in selTheme):
            bg = pygame.image.load("images/theme_Tarot/tarotwallpaper.jpg")
        pokemontheme = "selectedTheme=theme_Pokemon"
        if (pokemontheme in selTheme):
            bg = pygame.image.load("images/theme_Pokemon/pokemonwallpaper.jpg")
        pokertheme = "selectedTheme=theme_Poker"
        if (pokertheme in selTheme):
            bg = pygame.image.load("images/theme_Poker/pokerwallpaper.jpg")
        ffxivtheme = "selectedTheme=theme_Final Fantasy 14"
        if (ffxivtheme in selTheme):
            bg = pygame.image.load("images/theme_Final Fantasy 14/ffxivwallpaper.jpg")
        nfltheme = "selectedTheme=theme_NFL"
        if (nfltheme in selTheme):
            bg = pygame.image.load("images/theme_NFL/nflwallpaper.jpg")
        
        bg = pygame.transform.scale(bg, (self.screenWidth, self.screenHeight))
        window.blit(bg, (0,0))
        green = (0, 255, 0)
        red = (255, 0, 0)
        white = (255, 255, 255)
        black = (0, 0, 0)
        
        if self.difficulty == 0:
            matchTime = 30
        elif self.difficulty == 1:
            matchTime = 60
        else:
            matchTime = 45
            
        t = self.createTable()
        updateLivesStreakTimeScoreVisual(t, white, matchTime, window)

       

        minBorder = 70
        inBTween = 10
        scale = self.setCardScale(minBorder, t.x, t.y, inBTween)
        xDim = int(250 * scale)
        yDim = int(350 * scale)
        xSize = xDim + inBTween
        ySize = yDim + inBTween
        toXCenter = self.centerDeckX(xSize, t.x, self.screenWidth, minBorder)
        timeToFlip = int(3000 * scale)  # can't be too fast or frames don't register
        
        path_to_background_music_file = 'Sounds/'+str(self.selectedTheme)+'.mp3'
        background_music_path = Path(path_to_background_music_file)
       
        
        mixer.init()
        if background_music_path.is_file():
            mixer.music.load('Sounds/'+str(self.selectedTheme)+'.mp3')
        else: 
            mixer.music.load('Sounds/Mario.mp3')
        mixer.music.set_volume(self.volume/100)
        mixer.music.play(-1)
        
        t.showAll()
        tempTable = []
        for i in range(t.x):
            for j in range(t.y):
                t.table[j][i].col = i
                t.table[j][i].row = j
                tempTable.append(t.table[j][i])
                surface = t.table[j][i].image.convert()
                surface = pygame.transform.scale(surface, (xDim, yDim))
                window.blit(surface, ((minBorder + toXCenter) + xSize * t.table[j][i].col, minBorder + ySize * t.table[j][i].row))
        pygame.display.update()
        
        self.stopAllFor(2)
        if(not running):
            pygame.event.clear()
            return False
        self.animate.flip(tempTable, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
        

        timer = matchTime
        sTime = time.time()

        timeLeft = int(timer - (time.time() - sTime))

        streak = 0

        quitG = False
        
        path_to_victory_file = 'Sounds/'+str(self.selectedTheme)+' Victory.mp3'
        path_to_gameover_file = 'Sounds/'+str(self.selectedTheme)+' Gameover.mp3'
        victory_path = Path(path_to_victory_file)
        gameover_path = Path(path_to_gameover_file)
        
        while running:
            self.mainClock.tick(self.FPS)
            mouse = pygame.mouse.get_pos()
            updateLivesStreakTimeScoreVisual(t, white, timeLeft, window)

            if t.checkWin():
                for card in tempTable:
                    if not card.shown:
                        c = [card]
                        self.animate.flip(c, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                window.fill(self.boxColor.getCol(), (0, 0, self.screenWidth, 40))

                if len(t.selection) >= 2:
                    t.score = t.score + 100 + (50 * streak)
                    
                if self.gamemode == 1:
                    t.score = t.score + (t.lives * 100)
                    self.draw_text("Lives: " + str(t.lives), self.lifeFont, white, 5, 0, window)
                elif self.gamemode == 2:
                    t.score = t.score + (timeLeft * 10)
                    self.draw_text("Time: " + str(timeLeft) + "s", self.lifeFont, white, 5, 0, window)    
                elif self.gamemode == 3:
                    t.score = t.score + (t.lives * 100) + (timeLeft * 10)
                    self.draw_text("Lives: " + str(t.lives), self.lifeFont, white, 5, 0, window)
                    self.draw_text("Time: " + str(timeLeft) + "s", self.lifeFont, white, 5, 20, window)

                self.draw_text("Score: " + str(t.score), self.lifeFont, white, 105, 0, window)

               #self.draw_text_center("You win!", self.endFont, green, self.screenWidth / 2, self.screenHeight / 4, window)
                pygame.display.update()
                
                mixer.init()
                if victory_path.is_file():
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+' Victory.mp3')
                else: 
                    mixer.music.load('Sounds/Mario Victory.mp3')
                mixer.music.set_volume(self.volume/120)
                mixer.music.play()
                
                time.sleep(1)
                window.fill(self.boxColor.getCol())
                
                running, playAgain = self.endScreen(window, t.score, True, True)

                if playAgain:
                    mixer.init()
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+'.mp3')
                    mixer.music.set_volume(self.volume/100)
                    mixer.music.play(-1)
                    return Game.game(self, window)
                
                else:
                    return

            elif (t.lives == 0 or timeLeft <= 0):
                hiddenTable = []
                for card in tempTable:
                    if (not card.shown):
                        hiddenTable.append(card)

                self.animate.flip(hiddenTable, 1000, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)

                self.draw_text_center("You lose!", self.endFont, red, self.screenWidth / 2, self.screenHeight / 4, window)
                
                mixer.init()
                
                if gameover_path.is_file():
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+' Gameover.mp3')
                else: 
                    mixer.music.load('Sounds/Mario Gameover.mp3')
                
                mixer.music.set_volume(self.volume/120)
                mixer.music.play()
                self.stopAllFor(2)

                running, playAgain = self.endScreen(window, t.score, True, False)

                if playAgain:
                    mixer.init()
                    mixer.music.load('Sounds/'+str(self.selectedTheme)+'.mp3')
                    mixer.music.set_volume(self.volume/100)
                    mixer.music.play(-1)
                    return Game.game(self, window)
                
                else:
                    return

            else:
                t.update()
                for i in range(t.x):
                    for j in range(t.y):
                        surface = t.table[j][i].image.convert()
                        surface = pygame.transform.smoothscale(surface, (xDim, yDim))
                        t.table[j][i].rect = surface.get_rect()
                        t.table[j][i].makeRect((minBorder + toXCenter) + xSize * i, minBorder + ySize * j)
                pygame.display.update()
                
                if self.gamemode == 2 or self.gamemode == 3:
                    timeLeft = int(timer - (time.time() - sTime))

                if len(t.selection) >= 1:
                    if t.checkBomb():
                        
                        self.stopAllFor(1)
                        for c in t.selection:
                            if not (c.ID == "BOMB"):
                                cards = []
                                cards.append(c)
                                self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                        
                        t.selection.clear()
                        if self.gamemode == 1:
                            t.lives = t.lives - 1
                        elif self.gamemode == 2:
                            sTime = sTime - 10
                        elif self.gamemode == 3:
                            t.lives = t.lives - 1
                            sTime = sTime - 10
                            
                    if len(t.selection) >= 2:
                        isMatch = t.checkMatch()
                        if isMatch == 2:
                            self.stopAllFor(1)
                            if(running):
                                self.animate.flip(t.selection, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, False)
                                t.selection.clear()
                                if self.gamemode == 1 or self.gamemode == 3:
                                    t.lives = t.lives - 1
                                streak = 0
                        else:
                            if isMatch == 1:
                                match = t.selection[1].ID if t.selection[1].ID != "JOKER" else t.selection[0].ID
                                t.selection.clear()
                                for r in t.table:
                                    for c in r:
                                        if c.ID == match and not c.shown:
                                            cards = []
                                            cards.append(c)
                                            self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window, True)
                            t.selection.clear()
                            t.score = t.score + 100 + (50 * streak)
                            streak = streak + 1

                for row in t.table:
                    for c in row:
                        if (c.rect.collidepoint(mouse) and not c.shown):
                            for event in pygame.event.get():
                                if event.type == pygame.MOUSEBUTTONDOWN:
                                    cards = [c]
                                    self.animate.flip(cards, timeToFlip, xDim, yDim, minBorder, xSize, ySize, toXCenter, window,True)

                                    t.selection.append(c)
                                    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  
            
        es.join(0)
        return quitG
        
    def endScreen(self, window, score, sp, win):
        if sp:
            retryButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, self.screenHeight * 3/7), "Restart", self.buttonFont, "White", "#d7fcd4")
            scoresButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, (self.screenHeight * 3/7) + 110), "High scores", self.buttonFont, "White", "#d7fcd4")
            mmButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, (self.screenHeight * 3/7) + 220), "Return to mode select", self.buttonFont, "White", "#d7fcd4")
        else:
            mmButton = Button(pygame.image.load("Assets/ButtonBG.jpg"), (self.screenWidth/2, (self.screenHeight * 3/7) + 110), "Return to mode select", self.buttonFont, "White", "#d7fcd4")
        
        Score.saveScore(str(score))

        trails = []
        fireworks = [Firework(self.screenWidth, self.screenHeight) for i in range(1)]
        
        while True:
            self.mainClock.tick(self.FPS)
            mouse = pygame.mouse.get_pos()
            
            window.fill(self.boxColor.getCol())
            
            if sp:
                for button in [retryButton, scoresButton, mmButton]:
                    button.changeColor(mouse)
                    button.update(window)
            
            else:
                for button in [mmButton]:
                    button.changeColor(mouse)
                    button.update(window)
            
            if win:
                if sp:
                    self.draw_text_center("You win!", self.endFont, self.green, self.screenWidth / 2, self.screenHeight / 4, window)
                else:
                    self.draw_text_center("Game Over!", self.endFont, self.green, self.screenWidth / 2, self.screenHeight / 4, window)
                if randint(0, 70) == 1:  # create new firework
                    fireworks.append(Firework(self.screenWidth, self.screenHeight))
                
                update(window, fireworks, trails)
            
            else:
                self.draw_text_center("Game Over...", self.endFont, self.black, self.screenWidth / 2, self.screenHeight / 4, window)
                pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return [False, False]
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mixer.init()
                        mixer.music.load('Sounds/loading.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play()
                        return [False, False]
                    if event.key == pygame.K_r:
                        window.fill(self.boxColor.getCol())  # so cards show during lose screen
                        return [False, True]
                elif event.type == pygame.MOUSEBUTTONDOWN:
                   
                    if sp:
                        if scoresButton.checkForInput(mouse):
                            self.showScores(window, str(score))
                        if retryButton.checkForInput(mouse):
                            window.fill(self.boxColor.getCol())
                            return [False, True]
                    if mmButton.checkForInput(mouse):
                        mixer.init()
                        mixer.music.load('Sounds/loading.mp3')
                        mixer.music.set_volume(self.volume/100)
                        mixer.music.play()
                        return [False, False]
                    
    def createTable(self):
        if self.difficulty == 0:
            return Table(4, 3, self.selectedTheme, 5, self.difficulty, self.FPS)
        elif self.difficulty == 1:
            return Table(5, 5, self.selectedTheme, 10, self.difficulty, self.FPS)
        else:
            return Table(5, 5, self.selectedTheme, 6, self.difficulty, self.FPS)
        
    def showScores(self, window, pScore):        
        #self.draw_text_center("High scores", pygame.font.SysFont("Times New Roman", 40), self.white, self.screenWidth / 2, self.screenHeight / 10, window)
        
        posX = self.screenWidth - 370
        hsimg = pygame.image.load("images/theme_Developer/thehighscores.png")        
        
        scores = Score.readScores()
        textArea = ((self.screenHeight / 10) * 8) / 10
        
        while True:
            self.mainClock.tick(self.FPS)
            
            pygame.display.update()
            
            
            if posX > self.screenWidth / 10:
                posX = posX - 5
                window.fill(self.boxColor.getCol())
                window.blit(hsimg, (posX, self.screenHeight / 10))
        
            else:
                window.fill(self.boxColor.getCol())
                window.blit(hsimg, (self.screenWidth / 10, self.screenHeight / 10))
            
            pos = (self.screenHeight / 10) + 40
            for score in scores:
                if score == pScore:
                    self.draw_text_center(score, self.buttonFont, self.green, self.screenWidth / 2, pos, window)
                else:
                    self.draw_text_center(score, self.buttonFont, self.white, self.screenWidth / 2, pos, window)
                    
                pos = pos + textArea
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
