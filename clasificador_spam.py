# -*- coding: utf-8 -*-
"""
Clasificar correo
"""
import mailbox
import re
from functools import reduce
import operator
class ClasificadorSpam():

    def __init__(self,fichero_spam='spam.mbox',fichero_ham='ham.mbox', umbral=0.9,palabrasClave=15):
        self.umbral=umbral if umbral >=0 and umbral <1 else 0.9
        self.palabrasClave=palabrasClave if palabrasClave>0 else 15       
        self.S=0
        self.H=0
        self.patron='[^a-zA-Z0-9]'
        self.spam_words=dict()
        self.ham_words=dict()
        self.words_spam=[]
        self.words_ham=[]
        self.actualiza_valores_spam(fichero_spam)
        self.actualiza_valores_ham(fichero_ham)
#==============================================================================
#   Devuelve las palabras que aparecen en un fichero, agrupadas por mensaje
#   Es un método auxiliar de actualiza_valores
#==============================================================================          
    def palabras_fichero(self,fichero):
        correos=mailbox.mbox(fichero)
        words_subject=[set(re.split(self.patron,m['subject'].lower())) for m in correos]
        words_body=[set(re.split(self.patron,m.get_payload().lower())) for m in correos]
        words_new=[(words_subject[i].union(words_body[i])).difference({''})for i in range(len(words_subject))]
        return words_new
#==============================================================================
#   Calcula cuantas veces aparece una palabra en el conjunto de entrenamiento SPAM
#   Es un método auxiliar de actualiza_valores_spam
#   En otro caso, utilizar spam_words[palabra]
#==============================================================================  
     
    def aparece_palabra_spam(self,palabra):
        minus=palabra.lower()
        return sum(1 for i in range(self.S) if minus in self.words_spam[i] )
#==============================================================================
#   Calcula cuantas veces aparece una palabra en el conjunto de entrenamiento HAM
#   Es un método auxiliar de actualiza_valores_ham
#   En otro caso, utilizar ham_words[palabra]
#==============================================================================  
   
    def aparece_palabra_ham(self,palabra):
        minus=palabra.lower()   
        return sum(1 for i in range(self.H) if minus in self.words_ham[i] )

#==============================================================================
#   Actualiza el conjunto de entrenamiento SPAM con las palabras del fichero
#==============================================================================  
     
    def actualiza_valores_spam(self,fichero):
        words_fichero=self.palabras_fichero(fichero)
        self.words_spam.extend(words_fichero)
        self.S+=len(words_fichero)        
        for mensaje in words_fichero:
            for palabra in mensaje:
                self.spam_words[palabra]=self.aparece_palabra_spam(palabra)
 
#==============================================================================
#   Actualiza el conjunto de entrenamiento HAM con las palabras del fichero
#==============================================================================  
   
    def actualiza_valores_ham(self,fichero):
        words_fichero=self.palabras_fichero(fichero)
        self.words_ham.extend(words_fichero)
        self.H+=len(words_fichero)        
        for mensaje in words_fichero:
            for palabra in mensaje:
                self.ham_words[palabra]=self.aparece_palabra_ham(palabra)

#==============================================================================
#   Probabilidad de que aparezca una palabra dado que es spam
#   P(xw|y=si)
#==============================================================================  

    def prob_condicionada_spam(self,palabra):
        return 1.0*self.spam_words[palabra]/self.S if palabra in self.spam_words else 0.0
#==============================================================================
#   Probabilidad de que aparezca una palabra dado que es ham
#   P(xw|y=no)
#==============================================================================  

    def prob_condicionada_ham(self,palabra):
        return 1.0*self.ham_words[palabra]/self.H if palabra in self.ham_words else 0.0
#==============================================================================
#   Por revisar
#   Probabilidad de que aparezca una palabra dado que es spam
#   P(xw|y=si)
#   Con suavizado.    
#==============================================================================  

    def prob_condicionada_spam_suavizada(self,palabra):
        return 1.0*(self.spam_words[palabra]+1)/(self.S+2) if palabra in self.spam_words else 1.0/(self.S+2)
#==============================================================================
#   Por revisar
#   Probabilidad de que aparezca una palabra dado que es ham
#   P(xw|y=no)
#   Con suavizado.
#==============================================================================  

    def prob_condicionada_ham_suavizada(self,palabra):
        return 1.0*(self.ham_words[palabra]+1)/(self.H+2) if palabra in self.ham_words else 1.0/(self.H+2)
#==============================================================================
#   Probabilidad de spam del conjunto de entrenamiento
#   P(y=si)
#==============================================================================  
        
    def prob_spam(self):
        return 1.0*self.S/(self.S+self.H)
#==============================================================================
#   Probabilidad de ham del conjunto de entrenamiento
#   P(y=no)
#==============================================================================  
    def prob_ham(self):
        return 1.0*self.H/(self.S+self.H)

#==============================================================================
#   Probabilidad de spam condicionado a que esté la palabra
#   Se usa para caracterización
#   P(y|xw)
#==============================================================================
         
    def prob_spam_condicionada_palabra(self,palabra):
        prob_cond_spam=self.prob_condicionada_spam(palabra)
        prob_cond_ham=self.prob_condicionada_ham(palabra)
        if prob_cond_spam==0 and prob_cond_ham==0:
                res=0.5
        else:
                res=prob_cond_spam*self.prob_spam()/(prob_cond_spam*self.prob_spam()
                                       +prob_cond_ham*self.prob_ham())
        return res

#==============================================================================
#   Devuelve todas las palabras de un mensaje forma de conjunto
#==============================================================================
         
    def palabras_mensaje(self,mensaje):
        words_subject=set(re.split(self.patron,mensaje['subject'].lower()))
        words_body=set(re.split(self.patron,mensaje.get_payload().lower()))
        words_mensaje=words_subject.union(words_body).difference({''}) 
        return words_mensaje    
 
#==============================================================================
#   Devuelve las quince mejores palabras que clasifican un mensaje
#   En tuplas (palabra, probabilidad, caracterización)->Se cogen los más cercanos a 1
#   Si la probabilidad es menor que 0.5 se calcula la caracterización como
#   1 menos esa probabilidad para poder ordenarlos adecuadamente
#==============================================================================
 
    def palabras_mejor_clasifican_mensaje(self,mensaje):
        palabras_con_probabilidades=[(word,self.prob_spam_condicionada_palabra(word),
                                      self.prob_spam_condicionada_palabra(word)
                                  if self.prob_spam_condicionada_palabra(word)>0.5 
                                  else 1-self.prob_spam_condicionada_palabra(word))
                                  for word in self.palabras_mensaje(mensaje)]
        res=sorted(palabras_con_probabilidades, key=lambda palabra: palabra[2],
                   reverse=True)[0:self.palabrasClave] 
        return res

#==============================================================================
#   Clasificar un mensaje según lo especificado en el enunciado
#==============================================================================
    def prob_spam_mensaje(self,mensaje): 
        mejores_palabras=self.palabras_mejor_clasifican_mensaje(mensaje)
        probabilidad_spam=self.prob_spam()  * self.prod(self.prob_condicionada_spam_suavizada(palabra[0]) for palabra in mejores_palabras)
        probabilidad_ham=self.prob_ham()* self.prod( self.prob_condicionada_ham_suavizada(palabra[0]) for palabra in mejores_palabras)
        probabilidad=(probabilidad_spam)/(probabilidad_spam+probabilidad_ham)
        return probabilidad        
        
    def clasificar_mensaje(self,mensaje):
        return 1 if self.prob_spam_mensaje(mensaje)>self.umbral else 0
#==============================================================================
#   Clasificar correo de un fichero  
#==============================================================================
    def clasificar_correo(self,fichero):
       correos= mailbox.mbox(fichero)
       return [self.clasificar_mensaje(mensaje) for mensaje in correos]

#==============================================================================
#   Devuelve el producto de los valores que se pasan en el iterable  
#==============================================================================
    def prod(self,iterable):
        return reduce(operator.mul, iterable, 1)
      
