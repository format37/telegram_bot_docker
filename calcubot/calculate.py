import resource
import sys

try:
	res_limits = resource.getrusage(resource.RUSAGE_SELF)
	resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
	request = sys.argv[1]
	print( eval(request) )
except Exception as e:
	print(e)
