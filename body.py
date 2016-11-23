# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 14:15:40 2016

@author: Jake
"""

from bs4 import BeautifulSoup as bs
import requests, openpyxl, copy, os, os.path, csv
import easy_load




class Player(object):
    """
    Table object holds the table and all of its part, including the original html
    code for the table and the individual parts for each row and column. Table obj
    needs the original page html code, the table keyword, and the web scraper to use.
    OBJ STRUCTURE:
        -self.table: A dictionary, with each category as its key, and a list of
         data as its value.
        -self.order: A list containing the original order to the categories as
         listed in the table on fangraphs.com.
    self.table STRUCTURE:
        {Season Year: 
            {Team Name:
                {Stat Abreviation: X }
                }
            }
         
    NOTES:
        -Scraper can just be the tuple returned by our webscraper. We can use the 
         scraper itself to create the table object. This may be easier than having
         the scraper make the info. 
        -We could redefine the iterator of the table object so that we can iterate 
         through the rows and the columns.
        -Table __init__ needs to be changed so that it no longer calls the scraper. 
         the Table obj needs to be created by the scraper, not the other way around.
         We can change the init to recieve info from the scraper, rather than take
         the page, table, and scraper variables. 
    """
    def __init__(self, name):
        self.player_name = name
        self.id_dic = create_id_dic(os.path.join(os.path.dirname(__file__), 'PlayerID.xlsx'), 'PLAYERIDMAP')
        self.page = self._check_name(self.player_name, self.id_dic)
#        self.order = order # dic w/ key as table header, and value as ordered list of stats
        self._season_key = None
        self.data = []
        self.table_temps = {
            'dashboard': None,
            'standard': None,
            'advanced': None,
            'batted ball': None,
            'more batted ball': None,
            'win probability': None,
            'pitch type': None,
            'pitchf/x type': None,
            'pitchf/x velocity': None,
            'pitch values': None,
            'pitchf/x values': None,
            'pitchf/x values/100': None,
            'plate discipline': None,
            'pitchf/x plate discipline': None,
            'fielding': None,
            'advanced fielding': None,
            'inside edge fielding': None,
            'fan scouting': None,
            'value': None
                    }
        self.table = self.sportscraper(self.page)
        
    def __repr__(self):
        return '<Player Obj; Player: %s>' % (self.player_name)
        
    def __getitem__(self, index):
        """
        The Table Object makes two __getitem__ calls to gather the stat. It first
        takes the season, then the stat. It creates a database that contains the 
        teams the player played on in that season, and the stat specified by the 
        user. Ex: Table['2009']['R']
        """
        if self._season_key:
            temp = self.table[self._season_key]
            for i in temp.keys():
                # temp[i] is the team the player played on, temp[i][index] the stat.
                self.data.append({})
                self.data[len(self.data)-1][i] = temp[i][index]
            self._season_key = None # Reset
            return self.data
        else:
            self._season_key = index # Save first __getitem__ call
            self.data = [] # reset data list
            return self
            
    def __call__(self, seasons='all', stats='all', template=True):
        """
        When called, Table Obj takes a list (currently) of seasons and a list of
        stats that are returned as a single dictionary of dictionaries (our new, temp 
        database). Emphasis on "returned": this does not change the object in any way,
        it returns the data requested. 
        
        OUTLINE:
            -iterate through season lists and stat lists
            -create new dic to put our data in
            -first put a season dic (OrderedDic?) in new dic, then run through each
             team dic and pick up each stat.
            -return dic
        """
        temp = {}
        log = []
        if seasons == 'all':
            # If both seasons and stats set to 'all'
            if stats == 'all':
                # If template, return dashboard table
                if template:
                    temp = self.template()
                # Else, return whole database
                else:
                    temp = self.table
            # If only seasons set to 'all', collect all seasons, but specify stats
            else:
                for key in self.table.keys():
                    temp.setdefault(key, {})
                    if key == 'Total':
                        temp[key] = {}
                        # If a list of stats
                        if type(stats) in (list, tuple):
                            for stat in stats:
                                # Check if stat exists in database
                                if stat in self.table[key].keys():
                                    temp[key][stat] = self.table[key][stat]
                                    
                                # Else, add stat to log
                                else:
                                    log.append(stat)
                        # If one stat
                        elif type(stats) == str:
                            if stats in self.table[key].keys():
                                temp[key][stats] = self.table[key][stats]
                            else:
                                log.append(stats)
                                
                        # Handle error (not str or list)
                        else:
                            return 'ERROR: stats keyword not list type or string type.'
                    else:
                        for team in self.table[key].keys():
                            temp[key][team] = {}
                            # If a list of stats
                            if type(stats) in (list, tuple):
                                for stat in stats:
                                    # Check if stat exists in database
                                    if stat in self.table[key][team].keys():
                                        temp[key][team][stat] = self.table[key][team][stat]
                                    # Else, add stat to log
                                    else:
                                        log.append(stat)
                            # If one stat
                            elif type(stats) == str:
                                if stats in self.table[key][team].keys():
                                    temp[key][team][stats] = self.table[key][team][stats]
                                else:
                                    log.append(stats)
                               
                            # Handle error (not str or list)
                            else:
                                return 'ERROR: stats keyword not list type or string type.'
        
        else:
            # if partial list of season is given
            if type(seasons) in (list, tuple):
                for season in seasons:
                    if season == 'Total':
                        temp[season] = {}
                        # If a list of stats
                        if type(stats) in (list, tuple):
                            for stat in stats:
                                # Check if stat exists in database
                                if stat in self.table[season].keys():
                                    temp[season][stat] = self.table[season][stat]
                                    
                                # Else, add stat to log
                                else:
                                    log.append(stat)
                        # If one stat
                        elif type(stats) == str:
                            if stats in self.table[season].keys():
                                temp[season][stats] = self.table[season][stats]
                            else:
                                log.append(stats)
                                
                        # Handle error (not str or list)
                        else:
                            return 'ERROR: stats keyword not list type or string type.'
                    
                    elif season in self.table.keys():
                        temp.setdefault(season, {})
                        for team in self.table[season].keys():
                            temp[season].setdefault(team, {})
                            # if all stats are given
                            if stats == 'all':
                                for stat in self.table[season][team].keys():
                                    temp[season][team][stat] = self.table[season][team][stat]
                            # if partial list of stats
                            elif type(stats) in (list, tuple):
                                for stat in stats:
                                    if stat in self.table[season][team].keys():
                                        temp[season][team][stat] = self.table[season][team][stat]
                                    else:
                                        log.append(stat)
                            # only one stat
                            elif type(stats) == str:
                                if stats in self.table[season][team].keys():
                                    temp[season][team][stats] = self.table[season][team][stats]
                                else:
                                    log.append(stats)
                            else:
                                return 'ERROR: stats keyword not list type or string type.'

                    else:
                        log.append(season)
            # if only one season is given
            elif type(seasons) == str:
                if seasons in self.table.keys():
                    if seasons == 'Total':
                        temp[seasons] = {}
                        # If a list of stats
                        if type(stats) in (list, tuple):
                            for stat in stats:
                                # Check if stat exists in database
                                if stat in self.table[seasons].keys():
                                    temp[seasons][stat] = self.table[seasons][stat]
                                    
                                # Else, add stat to log
                                else:
                                    log.append(stat)
                        # If one stat
                        elif type(stats) == str:
                            if stats in self.table[seasons].keys():
                                temp[seasons][stats] = self.table[seasons][stats]
                            else:
                                log.append(stats)
                                
                        # Handle error (not str or list)
                        else:
                            return 'ERROR: stats keyword not list type or string type.'
                    
                    else:
                        temp.setdefault(seasons, {})
                        for team in self.table[seasons].keys():
                            temp[seasons].setdefault(team, {})
                            # all stats and one season
                            if stats == 'all':
                                for stat in self.table[seasons][team].keys():
                                    temp[seasons][team][stat] = self.table[seasons][team][stat]
                            # list of stats and one season
                            elif type(stats) in (list, tuple):
                                for stat in stats:
                                    if stat in self.table[seasons][team].keys():
                                        temp[seasons][team][stat] = self.table[seasons][team][stat]
                                    else:
                                        log.append(stat)
                            # one season and one stat
                            elif type(stats) == str:
                                if stats in self.table[seasons][team].keys():
                                    temp[seasons][team][stats] = self.table[seasons][team][stats]
                                else:
                                    log.append(stats)
                            else:
                                return 'ERROR: stats keyword not list type or string type.'

            else:
                return 'ERROR: stats keyword not list type or string type.'
                
        if log:
            print('Some arguements were not found in the database.')
            response = input('Would you like to read the log? [y/n]: ')
            if response.lower() in ('yes', 'y'):
                print('===============================Log: ')
                for entry in log:
                    print(str(entry))
                    
        return temp
        
    def _check_name(self, name, dic):
        """
        checks to see if there are multiple choices for the player by that name, 
        then prompts you which one you mean. Returns the correct page.
        """
        player_id = dic[name]
        return 'http://www.fangraphs.com/statss.aspx?playerid=' + str(player_id)
    
    def sportscraper(self, page='http://www.fangraphs.com/statss.aspx?playerid=1177&position=1B'):
        """
        Page= keyword should be variable. Keyword just for debugging.
        
        beautifulsoup objs:
            -soup: tables
            -chowder: headers
            -stew: table body
            -chunks: tr in table body
            -chili_code: all links within the table (headers not including season & team plus team & year stats in table )
            -cheese: value in chili_queso
            -chili_queso: stats in the table
        """
        dic = {}
   
        tables = [
        'dashboard',
        'standard', 
        'advanced',
        'batted ball',
        'more batted ball',
        'win probability',
        'pitch type',
        'pitchf/x type',
        'pitchf/x velocity',
        'pitch values',
        'pitchf/x values',
        'pitchf/x values/100',
        'plate discipline',
        'pitchf/x plate discipline',
        'fielding',
        'advanced fielding',
        'inside edge fielding',
        'fan scouting',
        'value'
            ]
        
        # Gather the page and convert to string
        res = requests.get(page)
        page = res.text
        

        table_index = 0
               
        
        soup = bs(page, 'html')
        table = soup.find_all('table')
        
        
        # Set up progress bar
        table_total = len(table)
        progress_bar = easy_load.progress_bar(table_total)
        
        for index, table_source in enumerate(table):
            # Trip Bit
            table_used = False
                        
            soup = bs(str(table_source), 'html')
            code = soup.find_all('th')
            for tag in code:
                progress_bar.paint_bar()                
                
                # if bugs arise check here!!!!!
                if tag.getText() == 'Team':
    
                    if '@' not in str(table_source):
                        stats = {}
                        stats_order = []
                        
                        # looks for headers
                        chowder = bs(str(table_source), 'html')
                        chow_code = chowder.select('th > a')
                        
                        # looks for body
                        stew = chowder.select('tbody > tr')
    
                        # collects stats headers and saves their order in a list
                        for stat_head in chow_code:
                            stats_order.append(stat_head.getText())
                            stats.setdefault(stat_head.getText(), None)
                        
                        for chunks in stew:
                            chili = bs(str(chunks), 'html')
                            # _code is the <a> assoc. w/ years and team
                            # _queso is the rows w/out <a> (the stats)
                            chili_code = chili.select('td > a')
                            chili_queso = chili.select('td[align="right"]')
    #                        print(chili_code.getText())
                            
                            
                            # Temp variable to hols season or Total key                            
                            season_temp = None
                            team_temp = None
                            # Skip these rows
                            if not 'ZiPS' in str(chunks) and not 'Steamer' in str(chunks) and not 'Depth Charts' in str(chunks):
    #                            print(chunks.getText())
                                # Grabs the Season Year and the Team played on
                                if not 'Total' in str(chunks):
    #                                print(chili_code[0].getText())
                                    if len(chili_code) >=2:
    #                                    print(chili_code[0].getText())
                                        season_temp = chili_code[0].getText()
                                        team_temp = chili_code[1].getText()
                                        dic.setdefault(chili_code[0].getText(), {})
                                        # Deepcopy to avoid updating a referenced dic, instead having a new dic replicated
                                        dic[chili_code[0].getText()].setdefault(chili_code[1].getText(), copy.deepcopy(stats)) 
    #                                else:
    #                                    print('HTML with less than 2 tags found:')
    #                                    print(chili_code)
    #                                    print(chili)
                                else:
    #                                print(chili_code[0].getText())
                                    season_temp = chili_code[0].getText()
                                    dic.setdefault(chili_code[0].getText(), copy.deepcopy(stats))
                
                                # Collect Stats themselves
#                                if len(chili_code) == 1:
#                                    print(chili_code[0].getText())
                                if len(chili_code) not in (0, 1): # Quick fix for empty chili_code and Postseason rows; May cause errors
                                    for index, cheese in enumerate(chili_queso):
                                        if cheese.getText() not in ('', '\xa0'):
                                            if season_temp != 'Total':
        #                                        print(chili_code[0].getText())
                                                if len(chili_code) <= 2:
        #                                           print(season_temp)
                                                    dic[season_temp][team_temp][stats_order[index]] = cheese.getText()
                                                    table_used = True
                                            else:
                                                dic[season_temp][stats_order[index]] = cheese.getText()
                                                table_used = True
                                        else:
                                            if season_temp != 'Total':
                                                if len(chili_code) <= 2:
                                                    dic[season_temp][team_temp][stats_order[index]] = None
                                                    table_used = True
                                            else:
                                                dic[season_temp][stats_order[index]] = None
                                                table_used = True
            # Update progress bar
            progress_bar.update(1)
            
            if table_used and table_index < len(tables):
                create_text('table_log', html=str(table_source))
                self.table_temps[tables[table_index]] = stats_order
                table_index += 1
                
        # Final progress bar
        progress_bar.paint_bar() 
        
        return dic
    
        """
        TODO:
        [ ] - Stat headings aren't scraped and saved to our table templates attribute
        in the Player object, which is required to use templates to create our csvs. 
        The problem occurs because of an inability to predict if a table is being saved
        in it's entirity or if it is being skipped. Without being able to predict if 
        the table is being saved, we cannot also predict if we should be saving the headers
        we scrape as well (headers are scraped first, and do not follow the logic of what
        is table is saved or not). Specifically, we have a list in the tables variable 
        that is recieving an index error because we are incorrectly calculating which 
        tables are being saved and which are not. 
        
        [ ] - Total doesn't work. It returns incorrect data, usually the data from the
        Fielding table, but there are other inconsistancies that do not make sense. For Ex:
        HR returns None, rather than a value, despite the fact that there are several 
        Total rows that contain an HR column. For now, ignore Total and come back to it.
        The rest of the scraper seems to work just fine. 
        
        [ ] - Fielding stats (on table Fielding and Advanced Fielding) are not being 
        collected during our scrape. This was done intentionally, but still needs to
        be fixed at some point. Our problem with Total rows discussed above is partially
        due to us not dealing with Fielding stats. The Total rows from Fielding tables
        are not ignored like the headers and stats are. 
        """                       

        
    def template(self, template='dashboard'):
        return self(seasons='all', stats=self.table_temps[template])
        
    def combine_tables(self, templates='all'):
        """
        Takes keyword templates, which must be a string 'all' or a list or tuple
        of strings with the table titles. 
        """        
        
        tables = [
        'dashboard',
        'standard', 
        'advanced',
        'batted ball',
        'more batted ball',
        'win probability',
        'pitch type',
        'pitchf/x type',
        'pitchf/x velocity',
        'pitch values',
        'pitchf/x values',
        'pitchf/x values/100',
        'plate discipline',
        'pitchf/x plate discipline',
        'fielding',
        'advanced fielding',
        'inside edge fielding',
        'fan scouting',
        'value'
            ]
            
        stats = []
        
        if templates == 'all':
            for table in tables:
                stats += self.table_temps[table]
                
        elif type(templates) in (list, tuple):
            for table in templates:
                stats += self.table_temps[table]
        else:
            return 'ERROR: templates keyword is not str \'all\' or a list or tuple type.'
        
        return stats

class Dugout(object):
    
    def __init__(self, name, dic):
        self.player = {}
        self.tables = {}
        self.stats = {}
        self.add_player(name)
        
        
    def add_player(self, name):
        """
        Creates player object and adds it to the player dictionary. Uses the name
        given at the prompt as the key to the player obj. 
        """
        self.player.set_default(name, '')
        self.player[name] = Player(name)
        
    def add_table(self, player, seasons, stats):
        """
        create_table takes a player name (str) and a list of stats to create a
        table for our self.table dictionary. Prompts the user for a table name, 
        and nests the table in the self.table dictionary like this:
            self.table = {
                            player_name: {
                                            table_name: table
                                                            }
                                            }
        """
        self.tables.setdefault(player, {})
        table_name = input('Please name your table: ')
        self.tables[player][table_name] = self.player[player](seasons, stats, False)
        self.display_table(self.tables[player][table_name])
        
    def display_table(self, table):
        # Temporary fix: make a prettier print later
        print(table)
        
    def compare(self):
        pass
    
    def create_csv(self):
        pass


"""
===============================================================================
                                FUNCTIONS
===============================================================================
"""


def create_id_dic(file, sheet):
    workbook = openpyxl.load_workbook(file)
    sheet = workbook.get_sheet_by_name(sheet)
    id_dic = {}
    for row in range(2, sheet.max_row + 1):
        name = 'B' + str(row)
        ID = 'I' + str(row)
        id_dic[sheet[name].value] = sheet[ID].value
        
    return id_dic
    
def create_text(file_name, db=None, html=None):
    name = file_name
    if db:
        for season in db.keys():
            with open('%s.txt' % name, 'w') as file:
                file.write('%s: ' % season)
                file.write(str(db[season]) + '/n')
                
    if html:
        if os.path.isfile('%s.txt' % name):
            with open('%s.txt' % name, 'a') as file:
                file.write(html)
                file.write('\n')
                file.write('\n')
        else:
            with open('%s.txt' % name, 'w') as file:
                file.write(html)
                file.write('\n')
                file.write('\n')
        
    return 'Done.'
     
def create_csv(player_name, db, template=[]):
    
    # Unpack into lists
    name = player_name
    headers = ['Season', 'Team']
    table = []    
    temp = ('blank')    
    
    # Create Headers   
    if not template:
        for season in db.keys():
            if season != 'Total':
                for team in db[season].keys():
                    if len(db[season][team]) > len(temp):
                        temp = (season, team)
        for stat in db[temp[0]][temp[1]]:
            headers.append(stat)
    
    else:
        assert type(template) in (list, tuple), 'ERROR: template keyword must be a list or tuple.'        
        headers += list(template)
    
    # Collect Stats
    for season in db.keys():
        if season == 'Total':
            row = []
            row.append(season)
            row.append(None)
            for stat in headers[2:]:
                if stat in db[season].keys():
                    row.append(db[season][stat])
                else:
                    row.append(None)

        else:
            for team in db[season].keys():
                if len(db[season][team]) > 2:
                    row = []
                    row.append(season)
                    row.append(team)
                    for stat in headers[2:]:
                        if stat in db[season][team].keys():
                            row.append(db[season][team][stat])
                        else:
                            row.append(None)
                    table.append(row)
                    
    # Order rows by Season
    table = sorted(table, key=lambda x: int(x[0]))
                          
    table.insert(0, headers)
    
    # Create the csv file
    with open('%s.csv' % name, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        for row in table:
            writer.writerow(row)
    print('Done.')
    
    
    

class Runtime(object):
    
    def __init__(self):
        self.cmds = {
            'new player': new_player,
            'new table': new_table,
            'help': user_help(),
            'templates': templates(),
            'export table': export_table,
            ('season', 'seasons'): season,
            ('stat', 'stats'): stat
                }
                
        self.templates = [
        'dashboard',
        'standard', 
        'advanced',
        'batted ball',
        'more batted ball',
        'win probability',
        'pitch type',
        'pitchf/x type',
        'pitchf/x velocity',
        'pitch values',
        'pitchf/x values',
        'pitchf/x values/100',
        'plate discipline',
        'pitchf/x plate discipline',
        'fielding',
        'advanced fielding',
        'inside edge fielding',
        'fan scouting',
        'value'
            ]
    
        name = input('Type in a Player (first and last name): ')

        # Session Variables
        self.active_player = name
        self.active_seasons = 'all'
        self.minor_league = True    
    
        self.dugout = Dugout(name)

    def run():
        pass
    
    def activate(self, new_player):
        pass
    
    def new_player(self, player):
        """
        Creates a new Player obj and adds it to the Dugout obj. Takes player name.
        """    
        self.dugout.add_player(player)
        self.active_player = player
        
    def new_table(self):
        """
        New_table takes a player name, then prompts the user for the table stats 
        or whether or not the table is a template based table. Creates
        the table and places it within Dugout.tables.
        """
        
        while True:
            table = input('Would you like to use a template? (y/n): ')
            if table.lower() in ('y', 'yes'):
                while True:
                    temp = input("Type in the name of your template, or type 'templates' for a list of available templates: ")
                    if temp.lower() == 'templates':
                        self.templates()
                    elif temp.lower() in self.templates:
                        if temp.lower() in self.dugout.tables[self.active_player]:
                            self.dugout.display_table(self.dugout.tables[self.active_player])
                            return
                        else:    
                            new_table = self.dugout.player[self.active_player].template(temp.lower())
                            self.dugout.tables[self.active_player][temp.lower()] = new_table
                            self.dugout.display_table(new_table)
                            return
                    else:
                        err = input('ERROR: {} is not a known template. Create new table? (y/n)'.format(temp.lower()))
                        if err.lower() in ('y', 'yes'):
                            table = err
            elif table.lower() in ('n', 'no'):
                while True:
                    name = input('Type your table name: ')
                    if name in self.dugout.tables[self.active_player]:
                        print('That name already exists.')
                    else:
                        stats_list = input('Type in your table stats seperated by \',\', or type \'all\' for all: ')
                        seasons_list = input('Type in your table seasons seperated by \',\' or type \'all\' for all: ')
                        stats = stats_list.split(', ')
                        seasons = seasons_list.split(', ')
                        new_table = self.dugout.player[self.active_player](seasons, stats)
                        self.dugout.tables[self.active_player] = new_table
                        self.dugout.display_table(new_table)
                        return
                
            else:
                return
        
        
    def user_help(self):
        """
        Returns a list of commands the user can use.
        """
        pass    
        
    def templates(self):
        """
        Returns a list of the template tables the user can use.
        """
        pass    
    
    def export_table(self, table, table_name=None):
        """
        Takes a dictionary obj 'table' and returns a csv file of the table. 
        """    
        pass
        
    def season(self, seasons, active_player):
        """
        Resets the active_seasons variable.
        """
        pass
    
    def stat(self, stat, seasons, active_player):
        """
        Returns the stats and their values for the active_player during the active
        seasons. 
        """
        pass    
    
if __name__ == '__main__':
    env = Runtime()
    env.run()
    


"""
===============================================================================
                                OUTLINING/NOTES
===============================================================================

Table Obj:
    -Table needs to be able to check which table to reproduce from the original
     html code. We could use a dictionary from the Sportscraper to run the proper
     scraper for that table. 
    -The webscraper could make the table object when it was done scraping. It 
     scrapes for the html code that contains the table, then runs another func
     that takes that html and divides it into the individual pieces it comprises
     of. This is then thrown into the creation of a table object. 

Player Obj:

Dugout Obj:

Sportscraper Obj:
    -Sportscraper needs to be built with functions that each look for specific tables
     in the html code, and perhaps even specific parts of specific tables. We can 
     hide these functions in a dictionary, and pass the key of which table we want
     to scrape for.
 
Major Keywords:
    -page: The actual webpage, in html, as a string.
    -scraper: the web scraper.
    -name: string of the player's name.
    -    
    
IDEAS:
    -We can use tuples in our verb dictionary or stat dictionary, so we can have 
     several possible commands equalling one stat, function, etc. For example, if
     we want batting average, we can have a dictionary that looks like dic={
     ('batting average', 'bavg', 'avg', 'average'): 227}, then use a loop of
     for k in dic.keys() and check if input in k. If input is in k, return 
     dic[k].
     
    -We could use pygame as an interface, or at least as a test interface we 
     can develop later. So long as our code works, all we need to do is map
     the various settings and keywords to menu options and buttons and we are
     set. We may need to create a chart creator program for pygame, but that 
     should be a lot more fun than hard. Like take the max of any value on
     the chart (like the max in the x value, or max of the y value) and divide
     the pixels accordingly. Then, calculate the height of each bar or line
     graph according to pixel approximations. Something like that. 
     
    -The webscraper could be an obj again. We could scrape per player and have
     it save the player it is associated with. We can grab a colleciton of all
     of the table elements (by using find_all to grab them one by one on the page)
     and then put them in a database that can be accessed as we need them. 
     
    -Current layout:
        DUGOUT-->Player Obj---->Table Obj (list)
                            |
                            --->Scraper--^
    

WHAT DOES IT NEED TO DO?:
    *BASIC*:
    -Collect stats from fangraphs, and have those stats available for customization.
    -Produce excel spreadsheets with stats of the user's choosing.
    -Allow easy comparison of stats between players.
    -
    
    *UNDERNEATH*:
    -Table objects need to collect all of the data from charts on fangraphs in an easily
     accessible way, as well as fascilitating easy comparison and managemant. 
    -Check for repeating statistic categories, so that we do not repeat them when our
     spreadsheet is produced. 
    -Dugout objects need to allow easy comparison of players through their table objs. 
     Dugout objs collect players and access the players as the user commands, then 
     accesses their table objects (also specified by the user). Stats are specified and
     routed to a part of the dugout object to be prepared and managed for saving to a
     spreadsheet. The dugout obj needs to be able to format the spreadsheet as well. Any
     spreadsheets already created by the user should also be saved so as not to waste 
     resources reproducing another. Same goes for (possible) charts. 
    
    *POSSIBLE*:
    -Allow use of charts for stats over time, and allow easy comparison charts between 
     players.
    -
    
STRUCTURE:
    When run, the app will take a player name. A Dugout object is immediately created, 
    and inside it a player object associated with the player is created. Then, the player
    object runs the sportscraper and recieves a dictionary of Table objects, each containing
    the data of the tables on that player's fangraph page. Each table can be collected 
    by using the correct key, named after the table title (i.e. 'Dashboard', or 'Pitch/FX').
   *ALTERNATIVELY*: We can save all data in one table object, which also contains the data
    needed to construct the 'default' tables from it's data. So instead of a table obj per
    table, we have one table obj that can construct the table at call. 
    
"""