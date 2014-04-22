import wave, struct, sys
#import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from subprocess import call
from scipy import fftpack
from scipy import interpolate
from scipy import signal
import numpy as np
import Tkinter as tk
import ttk
#from Tkinter import Tk, Frame, BOTH
'''
	** Intro **
	Application for Aalto bionics course.
	Sound analysis in a tkInter graphical ui.

	Please observe the import mess.

	The application hierarchy is as follows:
	 			run
		__________|_________
		/  	 	|		\
	.tkroot		.ui		.fcanvas
					

	** Description **
	Name-----------Class/type---------------Explanation
	run			program				The object where everything is inside
	.tkroot		Tk.TK()				the actual window
	.ui			Tk.Frame()			the user interface frame (above graph)
	.fcanvas		FigureCanvasTkAgg()		the graph "frame" (below ui)

	   
'''




def record_sound():		# Records audio from microphone to demo.wav
	path = 'demo.wav'
	"Records from the microphone and draws a wave form"
	prt("Recording")
	call(["arecord", "-d", "5", "-D", "hw:CARD=Camera,DEV=0", "-f", "S16_LE", "-c1" ,"-r44100", path])
	prt("Done recording")

class program:
	def __init__(self):
		self.tkroot = tk.Tk()
		self.tkroot.title("Bionics - ArtWhizkeez")
		#self.tkroot.geometry("800x400")
		self.ui = Visible( self.tkroot)
		self.tkroot.after(2000, self.update)
		self.fcanvas = FigureCanvasTkAgg(self.ui.figure, master=self.tkroot)
		self.fcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

	def loop(self):	# starts tk main loop
		self.tkroot.mainloop()
	def update(self):
		#self.app.canvas.delete(tk.ALL)
		self.tkroot.after(2000, self.update)
		#INSERT REALTIME STUFF HERE...

class Visible(tk.Frame):		#Extension on Tk.Frame
	def __init__(self, parent):
		tk.Frame.__init__(self, parent)#, background="red")
		self.parent = parent
		self.initUI()
		self.pack(fill=tk.BOTH, expand=1)
		#make rows expand when resizing window
		self.columnconfigure(0, weight=1)
		self.columnconfigure(1, weight=1)
		self.rowconfigure(1, weight=1)
		self.rowconfigure(0, weight=1)
		self.rowconfigure(2, weight=1)
		# call to start the updating "thread" 
		self.after(2000,parent.update)

	def close( self):
		self.destroy()
		self.quit()
		#sys.exit()
	
	def initUI( self):	# Creates the user interface
		#Set up UI 
		self.style = ttk.Style()
		self.style.theme_use("default")

		#Quit Button
		quitBtn = tk.Button(self, text="Quit", command=self.close)
		quitBtn.grid(row=0, column = 0, sticky=tk.W+tk.E)

		#Record Button
		recBtn = tk.Button(self, text="Record", command=record_sound)
		recBtn.grid(row=0, column = 1, sticky=tk.W+tk.E)

		#Plot buttokn
		plotBtn = tk.Button(self, text="Plot", command= lambda: plot_sound(self))
		plotBtn.grid(row=0, column = 2)
		#plotBtn2 = tk.Button(self, text="Plot", command= display_sound())
		#plotBtn2.grid(row=0, column = 3)
		#filter entries
		self.entry0 = tk.Entry(self)
		self.entry0.grid(row=1,column=0)
		self.entry1 = tk.Entry(self)
		self.entry1.grid(row=1,column=2)
		self.entry2 = tk.Entry(self)
		self.entry2.grid(row=1,column=1)
		self.entry0.insert(0,'demo.wav')
		self.entry1.insert(0,4000)
		self.entry2.insert(0,800)
		#CHECKBOX
		self.holdi = tk.IntVar()
		self.check = tk.Checkbutton(self, text='hold graph',variable=self.holdi)
		self.check.grid(row=2, column=1)
		#Figure for drawing the graphs in
		self.figure = Figure(figsize=(6,4), dpi=100)

		#Textbox
		self.text = tk.Text(self, width=50, height=5)
		self.text.grid(row=3,column = 0, columnspan=2,sticky=tk.W+tk.E+tk.N)

		self.text.insert(tk.END, "UI initialized\n")
		self.text.see(tk.END)
		#quitBtn.place(x=0, y=0)

def init():
	#Display	
	return program()

def prt(message):	#prints message to the textbox
	global run
	run.ui.text.insert(tk.END, message+"\n")
	run.ui.text.see(tk.END)

def plot_sound(self):	#Plots sound on graph 
	'''
	Here are some specifications and explanaitons:

	- sampling interval
		How long time has passed between measurements.
		We read unsigned values (see sample width) so our sampling interval is actually
		twice this number, because we ignore every other sample (because it is negative).
		ALternatively, the explanation is that we record stereo sound and need to ignore the other cannel.
		Although i'm not sure one mic-module can do that :D
		
		Sampling interval comes from sampling rate. which tends to be 44100 samples per second. so 44kHz (see the record_sound funciton)
		1 / sampling freq = sampling interval in seconds

	- sample width
		Tells in how many bytes the sound pressure values are mapped to integer values. 2 = two bytes. That means values ranging - 2^15 to +2^15 - 1
		In this program the values are signed. That's why we strip the negatively signed values with abs and use 2^(sampwidth / 2) as our scaling factor
	 	This is what i (Pietu) think is the reason to not use 2^16 but 2^8 as scaling.
		
	- samples
		Number of samples
	- duration
		how long (in seconds) is the audiofile

	'''
	global run
	#path = 'demo.wav'
	path = run.ui.entry0.get()
	#Open file
	try:
		wave_file = wave.open(path, 'rb')
		# sample spacing
		sampling_interval = 1./wave_file.getframerate()
		sampling_frq = wave_file.getframerate()
		#Sample width
		sampwidth = wave_file.getsampwidth()
		# Number of samplepoints
		samples = wave_file.getnframes()
	except IOError:
		prt('no such file')
		return
	# Duration
	dur = samples / float(wave_file.getframerate())
	prt("Wave duration "+str(dur)+"s")

	#Read data values
	X = []
	Y = []
	for i in range(samples):
	   d = wave_file.readframes(1)
	   Y.append(struct.unpack("<h", d)[0])
	   X.append(i * sampling_interval)
	wave_file.close()
	
	#CALCULATE
	'''
		the DATA is in a list (array if you wish).
		lists are accessed listname[index]. You read parts of lists by listname[start:stop]

		amp = amplitude or tiheysfunktio. How many occurences of this frequency are there
		frq = the corresponding frequency
	'''
	amp = fftpack.fft(Y)/samples		#fourier transform the original signal. Scale so that it does not depend on the signal or sampling freq
								#I do not understand this. On the web this relates to MATLAB not scaling fft output by length of input
								#wtf i do not want to /samples
	amp = amp[0:samples/2]	#chop of half of spectrum (it's symmetric. feature of fft or something)
	amp = amp / (2**(sampwidth*8/2))		#apply scaling factor (see above for explanation)
	
	frq = fftpack.fftfreq(amp.size, sampling_interval * 2)				#find corresponding frequencies
	#frq = np.linspace(0.0, 1.0/(2.0 * sampling_interval), samples/2)  	#this would have worked aswell

	max_frq = int(run.ui.entry1.get())
	min_frq = int(run.ui.entry2.get())
	#SCREEN the wanted portion of spectrum
	hzs = (samples/2) / (1.0 / (2.0 * sampling_interval))	#herz per sample. So if i want to chop of 5hz from beginning. i remove 5*hzs samples
	amp = amp[0:hzs*max_frq]		#here we remove all freq above 11kHz
	frq = frq[0:hzs*max_frq]		#the x and y lists need to have equal amount of data

	#MASK or apply treshold (todo)
	mask = abs(amp) > 10		
	#amp = amp[mask]



	#ABSOLUTE
	amp = abs(amp)
	#LOWPASS
	#h = signal.firwin(numtaps=int(run.ui.entry0.get()), cutoff=float(run.ui.entry1.get()), window="hamming")
	#filtered = signal.lfilter(h,1,amp)
	
	#aapoa ja latea
	''' jakaa datan seitsemaan osaan ja etsii maksimit '''
	vali_pituus = len( frq) // 15
	aapomax = []
	aapomax_v = []
	mediaani = []
	#MEDIAAN
	for i in range(len(frq)):
		valin_data = amp[max(i-400,0):min(len(frq),i+400)] 
		mediaani.append(np.median(valin_data))

	#DOWNSAMPLE
	#amp.reshape(-1, 200)
	#frq.reshape(-1, 200)
	amp=signal.decimate(amp,10)
	frq=signal.decimate(frq,10)
	mediaani=signal.decimate(mediaani,10)
	#filtered=signal.decimate(filtered,10)
	
	

	#ANALYZE PEAKS fp,ax "method"
	try:
		#We use 2 methods for peak detection	
		peaks_fp = signal.find_peaks_cwt(amp, np.arange(2,10))
		peaks_ax=signal.argrelextrema(amp,np.greater)

		#prt(str(peaks_fp))
		#prt(str(peaks_ax))

		peak_val_fp = amp[peaks_fp]
		peak_val_ax = amp[peaks_ax]

	except AttributeError:
		prt('some error in signal analysis :(')
	#SOME OTHERKIND OF PEAK ANALYSIS
	#minimas = signal.argrelmin(amp)

	#for i in minimas:
		#print(i,i//15, "a")

	#DA ANALYSIS
	''' katsotaan mitka maksimit ovat mediaanin ylapuolella'''
	data_x = []
	data_y = []
	for i in range(0,len(frq)):
		if (amp[i] > mediaani[i]):
			data_x.append(frq[i])
			data_y.append(amp[i]-mediaani[i])
	hzs = len(data_y)/float(max_frq)
	prt(str(hzs))
	for i in range(0,int(hzs*min_frq)):
		data_y[i] = 0
	data_y2=signal.decimate(data_y,10)
	data_x2=signal.decimate(data_x,10)
	#data_x = frq[hzs*800:5000*hzs]
	#data_y = amp[hzs*800:5000*hzs]

	data_peaks = signal.find_peaks_cwt(data_y2, np.arange(1,10))
	#data_peaks=signal.argrelextrema(data_y,np.greater)
	#some spline interpolation testing that doesn't work
	#amp_s = interpolate.UnivariateSpline(frq,amp,s=3)
	#amp=amp_s(frq)
		

	
	
	#DRAW
	if (run.ui.holdi.get() == 0):
		run.ui.figure.clf()
	prt(str(run.ui.holdi.get()))
	kuvaaja = run.ui.figure.add_subplot(211)
	kuvaaja.set_title('Spectrum')
	#kuvaaja.plot(frq, abs(amp))
	kuvaaja.plot(frq, amp)
	kuvaaja.plot(frq, mediaani)
	#kuvaaja.plot(frq, filtered)
	kuvaaja.hold(True)
	kuvaaja.grid()
	kuvaaja.set_xlabel('frequenzy [Hz]')
	#kuvaaja.plot(peaks[0],amp[peaks[0]],'ro')
	#kuvaaja.plot(frq[peaks_fp],amp[peaks_fp],'ro')
	#kuvaaja.plot(frq[peaks_ax],amp[peaks_ax],'gx')

	#KUVAAJA 2
	kuvaaja2 = run.ui.figure.add_subplot(212)
	kuvaaja2.set_title('Poweer')
	#kuvaaja2.plot(frq, np.log(amp)**2)
	#kuvaaja2.plot(data_x, data_y)
	kuvaaja2.plot(data_x2, data_y2)
	kuvaaja2.plot(data_x2[data_peaks],data_y2[data_peaks],'ro')
	#kuvaaja2.plot(data_x[data_peaks[0]],data_y[data_peaks[0]],'ro')
	kuvaaja2.grid()
	kuvaaja2.set_xlabel('frequenzy [Hz]')
	#aapomax
	#kuvaaja.plot(aapomax,aapomax_v,'bo')
	run.fcanvas.show()

	#JONKINLAINEN MATERIAALIANALYYSI
	''' vetailee kolmen ensimmaisen piikin suhteellisia eroja. 750hz, 1550hz ja 2225 hz'''
	arvo1 = data_y2[data_peaks[1]] / data_y2[data_peaks[0]]
	arvo2 = data_y2[data_peaks[2]] / data_y2[data_peaks[0]]
	prt(str(data_x2[data_peaks[0:5]]))
	prt('parametrit '+str(arvo1)+" "+str(arvo2))
	materiaalit = [[7.46,0.5, "puuta"],[5.85,1.15, "metallia"], [9.75, 0.799, "pahvia"]]
	dist_max = 100
	material = -1
	for mat in materiaalit:
		dist = abs(mat[0]-arvo1) + abs(mat[1]-arvo2)
		if (dist < dist_max):
			dist_max = dist
			material = mat[2]
		prt(str(dist))
	prt('luulen etta tama on '+str(material))	

	#run.fcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
	#fig.fcanvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)			#left here because i do not know what this does but i should
	
	prt('waveform plotted')

def display_sound():
	path = 'demo.wav'
	"Draws the wave forms from sound data"
	#Read in the data
	wave_file = wave.open(path, 'rb')
	sampling_interval = 1./wave_file.getframerate()
	# Number of samplepoints
	N = wave_file.getnframes()
	# sample spacing
	T = sampling_interval
	x = np.linspace(0.0, N*T, N)
	X = []
	Y = []
	for i in range(N):
	   d = wave_file.readframes(1)
	   Y.append(struct.unpack("<h", d)[0])
	   X.append(i * sampling_interval)
	wave_file.close()

	#plot amplitude vs time
	plt.figure(1)
	plt.plot(X,Y)
	plt.title('sound')
	plt.xlabel('time [s]')
	plt.show()

	#plot fft
	yf = fftpack.fft(Y)
	xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
	plt.plot(xf, 2.0/N * np.abs(yf[0:N/2]))
	plt.grid(row=6)
	#plt.pack()
	plt.xlabel('frequenzy [Hz]')
	plt.show()



if __name__ == '__main__':
	run = init()
	run.loop()
