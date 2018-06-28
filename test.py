import sys
import pdb

class apps():
	def __init__(self, hos):
		self.hos=hos
		self.del_data()
	def del_data(self):
		try:
			open("3.txt",'r')

		except Exception as e:
			pdb.set_trace()
			print(e)
			sys.exit()
	
		
		print("a")


if __name__ == '__main__':
	a=apps("fw")
