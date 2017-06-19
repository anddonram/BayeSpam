# -*- coding: utf-8 -*-
"""
Created on Sat May 14 12:52:59 2016

@author: Andrés
"""
import clasificador_spam
spam=clasificador_spam.ClasificadorSpam()
resultados=spam.clasificar_correo('news.mbox')
print(resultados)