import os, sys


from PySide6.QtCore import *
from PySide6.QtWidgets import QWidget, QApplication, QGridLayout
from PySide6.QtUiTools import QUiLoader
from scipy.io import wavfile
import scipy.fftpack as fourier
import serial
import time
import threading
import pyaudio
import wave
import numpy as np
import pylab
import winsound
import sounddevice as sd
import soundfile as sf
import seaborn as sns
from matplotlib import pyplot as plt
sns.set_style( 'darkgrid' )

from scipy import signal
import sounddevice as sd

nombre_grabacion='Grabacion.wav'




def graph_spectrogram(wav_file):
        sound_info, frame_rate = get_wav_info(wav_file)
        pylab.figure(num=None, figsize=(19, 12))
        pylab.subplot(111)
        pylab.title('spectrogram of %r' % wav_file)
        pylab.specgram(sound_info, Fs=frame_rate)
        #pylab.savefig('spectrogram.png')
        pylab.show()

def get_wav_info(wav_file):
        wav = wave.open(wav_file, 'r')
        frames = wav.readframes(-1)
        sound_info = pylab.frombuffer(frames, 'int16')
        frame_rate = wav.getframerate()
        wav.close()
        return sound_info, frame_rate

class Ventana( QWidget ) :

    def __init__( self ) :
        super( Ventana, self ).__init__()

        loader = QUiLoader()
        self.gui = loader.load( "panel.ui", None )  # panel.ui debe estar en la misma carpeta

        # Define un layout en Ventana y coloca alli la interfaz creada con QtDesigner
        grid = QGridLayout()
        grid.setContentsMargins( 0, 0, 0, 0 )
        grid.addWidget( self.gui )
        self.setLayout( grid )


        self.setWindowTitle( 'Panel de configuración' )

        self.grabacion = 0
        QObject.connect( self.gui.pbComArduino, SIGNAL( "pressed()" ), self.slot_arduino_Com )
        QObject.connect( self.gui.pbReproducir, SIGNAL( "pressed()" ), self.slot_reproducir )
        QObject.connect( self.gui.pbGraficar_Tiempo, SIGNAL( "pressed()" ), self.slot_graficar_tiempo )
        QObject.connect( self.gui.pbGraficar_Frec, SIGNAL( "pressed()" ), self.slot_graficar_frecuencia )
        QObject.connect( self.gui.pbGraficar_Espec, SIGNAL( "pressed()" ), self.slot_graficar_espectograma )
        


    def slot_arduino_Com(self) :
        #threading.Timer(1,Timer_Interrupt).start()
        serialArduino=serial.Serial("COM4",9600)
        time.sleep(1)
        while True:
            cad=serialArduino.readline().decode('utf-8').strip() #Strip elimina espacios en blanco y saltos
            print(cad)

            #Try para informar errores (ej en conversion a float) y continua el proceso
            try:
                volt=float(cad)
                if(volt>2.4):        
                    print("Valor Detectado: "+cad)
                    self.gui.pantalla.setText(cad) # Imprime valor detectado en Display
                    time.sleep(2)
                    #break
                    self.slot_grabarAudio()
                    break
            except:
                 print("error conversion") 
                


    def slot_reproducir( self ) :

        filename = nombre_grabacion
        data, fs = sf.read(filename, dtype='float32')  
        sd.play(data, fs)
        status = sd.wait()

    def slot_graficar_espectograma( self ) :

        filename = nombre_grabacion
        graph_spectrogram(filename)

    def slot_graficar_frecuencia( self ) :

        filename = nombre_grabacion

        Fs,data=wavfile.read(filename)
        Audio_m=data[:,0]

        L=len(Audio_m)

        Ts=0.001
        n=Ts*np.arange(0,L)

        #fig,ax=plt.subplots()
        #plt.plot(n,Audio_m)
        #plt.xlabel('Tiempo(s)')
        #plt.ylabel('Audio')

        gk=fourier.fft(Audio_m)
        M_gk=abs(gk)
        M_gk=M_gk[0:L//2]

        F=(Fs/L)*np.arange(0,L//2)
        fig,bx=plt.subplots()
        plt.plot(F,M_gk)
        plt.xlabel('Frecuencia', fontsize='14')
        plt.ylabel('Amplitud', fontsize='14')
        plt.show()

    def slot_graficar_tiempo( self ) :
        fs, audioClean = wavfile.read(nombre_grabacion)
        samples = len(audioClean)
        t = np.arange(0, samples/fs, 1/fs)
        plt.plot(t, audioClean)
        #fig.patch.set_facecolor('white')

        plt.plot(t, audioClean)
        plt.title('Audio dominio del tiempo')
        plt.xlabel('Tiempo [s]')
        #plt.xaxis.set_label_coords(1.05, -0.025)
        plt.ylabel('Amplitud')
        plt.grid(True)
        plt.show()

    def slot_grabarAudio( self) :

        print("*** GRABACION EN CURSO ****")
        audio=pyaudio.PyAudio() #iniciamos "PyAudio",creando asi una instancia de la clase PyAudio
        FORMAT=pyaudio.paInt16 # Se define formato del audio  en enteros de 16 bits
        CHANNELS=2 # 2 Canales de 16 bits
        RATE=int(self.gui.textFrecuencia.toPlainText()) #Frecuencia de muestreo de 44100 Hz y 16 bits por cada canal
        CHUNK=1024 # Frames de 1024 bits
        duracion=float(self.gui.textDuracion.toPlainText()) # Duracion de la grabacion, convierte texto en tipo float
        archivo=nombre_grabacion # Definimos el  nombre del archivo

        stream=audio.open(format=FORMAT,channels=CHANNELS,    # Se abre un flujo de audio para la grabación, 
                            rate=RATE, input=True,            # que dependera de los parámetros definidos en la etapa anterior
                            frames_per_buffer=CHUNK)
        print("grabando...") # Imprime mensaje de que la grabacion esta en curso
        frames=[] # se crea un lista vacia para almacenar las muestras de audio
        for i in range(0, int(RATE/CHUNK*duracion)):
            data=stream.read(CHUNK)
            frames.append(data)
        print("grabacion terminada")
        #DETENEMOS GRABACION
        stream.stop_stream()
        stream.close()
        audio.terminate()

        #CREAMOS/GUARDAMOS EL ARCHIVO DE AUDIO
        waveFile = wave.open(archivo, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()




    def keyPressEvent( self, e ) :

        if e.key() == Qt.Key_Escape :
            self.close()


# Función main que se ejecuta al iniciar la aplicación
if __name__ == '__main__':


    # Este objeto representa a la aplicación
    app = QApplication( sys.argv )

    os.chdir( os.path.dirname( os.path.abspath( __file__ ) ) )

    # Creamos y visualizamos el objeto Ventana que contiene la interfaz creada en QtDesigner
    ventana = Ventana()
    ventana.show()

    #arduino_Com()
 


   

    sys.exit( app.exec_() )