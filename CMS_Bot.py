import os, sys, time as t, logging as log, PySimpleGUI as sg
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
# chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument('--headless')

##################### Setup ########################

def setup_custom_logger(name):
    fm = log.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                       datefmt='%d-%m-%Y %H:%M:%S')
    h = log.FileHandler(name, mode='w')
    h.setFormatter(fm)
    sh = log.StreamHandler(stream=sys.stdout)
    sh.setFormatter(fm)
    l = log.getLogger(name)
    l.setLevel(log.DEBUG)
    l.addHandler(h)
    l.addHandler(sh)
    return l

logdir = Path.cwd() / 'logs'
if not Path(logdir).is_dir():
	logdir.mkdir()

fn = __file__.split('\\')[-1].split('.')[0] # filename minus .py
logname = 'logs/%Y-%m-%d - %H-%M-%S - ' + f'{fn}.log' # date formatted log
l = setup_custom_logger(datetime.now().strftime(logname))

# location of icon file for windows
icon_file = 'icon/wave.ico'

# set relative path for chromedriver executable file, otherwise its not on other user's system PATH
def driver_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

##################### Bot Commands ########################

class CMSBot:
	def __init__(self):
		self.b = webdriver.Chrome(options=chrome_options, executable_path=driver_path('./driver/chromedriver.exe'))

	def edit(self, ID):
		b = self.b
		url = 'http://newcms.warc.com/content/edit'
		b.get(url)
		l.info(f"requested url: '{url}'")
		b.implicitly_wait(5)
		l.info(f'-> editing {ID}')
		g = b.find_element_by_name('LegacyId')
		g.clear()
		g.send_keys(ID)
		g.send_keys(Keys.RETURN)
		t.sleep(1)

	def save(self):
		b = self.b
		t.sleep(1)
		b.find_element_by_xpath('//span[@onclick="onSaveClicked()"]').click()
		l.info('Saved changes')
		t.sleep(2)

	def bullets(self):
		b = self.b
		# check if button clickable and text present in box
		b.find_element_by_link_text('Summary').click()
		l.info("clicked [Summary] (Expand)")
		b.find_element_by_id('GenerateBullets').click()
		l.info("clicked [Generate Bullets]")
		t.sleep(1)

	def dates(self, value):
		b = self.b
		b.find_element_by_id("PublicationDate").send_keys(value)
		b.find_element_by_id("LiveDate").send_keys(value)
		t.sleep(1)

	def additional_info(self, award):
		b = self.b
		i = b.find_element_by_id('AdditionalInformation')
		v = i.get_attribute('value') # get existing info
		i.clear()
		l.info('existing info - ' + v)
		for x in ['Entrant, ','Shortlisted, ']:
			v = v.replace(x, '')
		i.send_keys(award + ', ' + v) # append award and strip existing Shortlisted if present
		l.info('appending - ' + award)
		n = b.find_element_by_id('AdditionalInformation').get_attribute('value')
		l.info('new info - ' + n)

##################### Generate Bullets ########################

def generate_bullets_window():

	cms = CMSBot()

	layout = [
		[sg.Text('Paste a column of IDs below:')],
		[sg.InputText()],
		[sg.Submit(), sg.Cancel()]
	]

	window = sg.Window(
		'Generate Bullets',
		layout,
		icon=icon_file,
		keep_on_top=True,
		grab_anywhere=True
	) 

	while True:
		event, values = window.read()

		if event in ('Cancel', None):
			break

		if event == 'Submit':
			IDs_input = values[0]
			IDs = IDs_input.strip().split('\n')

			for ID in IDs:
				# checks ID is 6 digits
				if len(ID) == 6:
					
					cms.edit(ID)
					t.sleep(1)
					# cms.bullets() # needs checks
					t.sleep(1)
					cms.save()
					t.sleep(1)
					
				else:
					l.info('- ID was not 6 digits long')
					sg.popup('IDs need to be 6 digits long', keep_on_top=True)

			sg.popup('Generated bullets for IDs:', IDs_input)

	cms.b.quit()
	l.info('- exited browser correctly')
	window.close()


######################## Change Metadata ############################

def change_metadata_window():

	cms = CMSBot()
 
	layout = [
		[sg.Output(size=(42,18))],
		[sg.Text('Paste a column of IDs and select the status of entries')],
		[sg.Text('IDs'), sg.InputText(focus=True)],
		[sg.Frame(layout=[[sg.Text('ddmmyyyy'), sg.InputText()]],
			title='Live Date',
			title_color='white')],
		[sg.Frame(layout=[
			[sg.Radio('Shortlisted', 'R', key='R1', default=False),
			sg.Radio('Entrant', 'R', key='R2', default=False)]],
			title='Status',
			title_color='white',
			relief=sg.RELIEF_SUNKEN,
			tooltip="Select whether to add 'Shortlisted' or 'Entrant' to Additional Information field.")], 
		[sg.Submit(), sg.Cancel()]
	]

	window = sg.Window('Change Metadata',
								layout,
								icon=icon_file,
								keep_on_top=True,
								grab_anywhere=True)    
	
	while True:
		event, values = window.read()

		if event in ('Cancel', None):
			break

		if event == 'Submit':
			print('Changing metadata for IDs:\n' + values[0])
			t.sleep(1)

			IDs_input = values[0]
			IDs = IDs_input.strip().split('\n')
			date = values[1]

			for ID in IDs:
				# checks ID is 6 digits
				if len(ID) == 6:
					cms.edit(ID)

					# if a Radio button is selected, append string to additional info field
					if values['R1'] == True:
						cms.additional_info('Shortlisted')
					elif values['R2'] == True:
						cms.additional_info('Entrant')

					# if valid date in dd/mm/yyyy format (8 digits), change date, otherwise pass or print message
					if str(date) == '':
						pass
					elif len(str(date)) == 8:
						cms.dates(date)
					else:
						print('date must be 8 digits in ddmmyyy format')

					# t.sleep(1)
					# cms.save()
					# t.sleep(1)
					
				elif len(ID) < 6:
					print('- ID was not 6 digits long')

	cms.b.quit()
	l.info('- exited browser correctly')
	window.close()

######################## Main Window ############################

def main():
	'''
	# INSTRUCTIONS
	- all you do is select a script
	  and select whichever settings you want
	  paste a column of IDs into the input field
	  hit Submit or Enter
	- the script will automatically interact with the IDs in the cms
	- our cms can only be accessed through vpn
	'''
	# theme_previewer()
	sg.theme('DarkTeal2') 

	layout = [
		[sg.Frame(
			title='Edit Functions',
			title_color='white',
			relief=sg.RELIEF_SUNKEN,
			layout=[[sg.Button('Bullets'), sg.Button('Metadata'), sg.Button('Videos')]]
		)],
		[sg.Frame(
			title='Batch Edit Functions',
			title_color='white',
			relief=sg.RELIEF_SUNKEN,
			layout=[[sg.Button('Add Content'), sg.Button('Set Live')]]
		)],
		[sg.Exit()]
	]

	window = sg.Window('CMS Bot',
						layout,
						icon=icon_file,
						resizable=True,
						keep_on_top=True,
						grab_anywhere=True)

	while True:
		try:
			event, values = window.read()
		
			if event in ('Exit', None):
				break
			if event == 'Bullets':
				pass
				# generate_bullets_window()
			if event == 'Metadata':
				change_metadata_window()
			if event == 'Videos':
				pass
			if event == 'Set Live':
				pass
			if event == 'Add Content':
				pass

		except Exception as e:
			l.error(e)
			sg.popup('An error occured, please see log file.', keep_on_top=True)

	window.close()

if __name__ == '__main__':
	main()