import resource
from sys import argv
from user_defined import *
import pandas as pd
import numpy as np
import scipy
from scipy import stats
import random
import datetime as dt
import statistics
import ast
import math
import sympy
import json
import re

try:
	res_limits = resource.getrusage(resource.RUSAGE_SELF)
	resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
	request = argv[1]
	print( eval(request) )
except Exception as e:
	print(e)
