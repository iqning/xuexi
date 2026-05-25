#如何忽略大小写进行验证判断=>upper()方法可以将字符串中的小写字母转换为大写字母
# verify_code="xAd1"
# user_input=input(f"请输入验证码({verify_code})：")
# if verify_code.upper()==user_input.upper():
#     print("验证成功！")
# else:
#     print("验证失败！")
#字符串替换=>strip方法可以去掉字符串两端的空格，split()方法可以将字符串按照指定的分隔符切割成一个列表
str1="  hello world  "
str2=str1.strip()
str3=str2.split(" ")
print(str2)
print(str3)
#字符串替换=>replace()方法可以将字符串中的指定子串替换为另一个子串
str4="I love Python"
str5=str4.replace("Python","Java")
print(str5)
#字符串切割=>split()方法可以将字符串按照指定的分隔符切割成一个列表 
str6="apple,banana,orange"
str7=str6.split(",")
print(str7)
#查找和判断=>find()方法可以返回指定子串在字符串中第一次出现的位置，如果没有找到则返回-1
str8="Hello,how are you?" 
index=str8.find("how")#如果找到了，返回的是子串的起始位置，如果没有找到，返回的是-1
if index!=-1:
    print(f"找到了，位置是{index}")
else:    
    print("没有找到")
#列表的概念=>list()函数可以将一个可迭代对象转换为一个列表
str9="Python"  
list1=list(str9)
print(list1)
#也有索引和切片=>索引可以通过下标访问列表中的元素，切片可以通过指定起始位置和结束位置来获取列表中的一部分元素
list2=[1,2,3,4,5]  
print(list2[0])#索引从0开始
print(list2[1:4])#切片获取索引1到3的元素
#列表用for进行遍历=>for循环可以遍历列表中的每个元素
list3=["apple","banana","orange"]
for fruit in list3:
    print(fruit)
#列表的常用方法=>append()方法可以在列表末尾添加一个元素，remove()方法可以删除列表中的一个元素，sort()方法可以对列表进行排序
list4=[3,1,4,2,5]  
list4.append(6)
print(list4)
list4.remove(3)
print(list4)
list4.sort()
print(list4)
#元组的概念=>元组是一种不可变的序列类型，使用圆括号()定义
tuple1=(1,2,3,4,5)
print(tuple1)
#元组的特点=>元组中的元素不能修改，元组可以包含不同类型的元素，元组支持索引和切片
print(tuple1[0])#索引从0开始
print(tuple1[1:4])#切片获取索引1到3的元素
#元组的应用=>元组可以用来存储一组相关的数据，例如一个人的姓名、年龄和性别，可以用一个元组来表示
person=("Alice",30,"男")
print(person)
#字典的概念=>字典是一种键值对的数据结构，使用花括号{}定义
dict1={"name":"Alice","age":30 ,"gender":"男"}
print(dict1)
#字典的特点=>字典中的键必须是唯一的，字典中的值可以是任意类型，字典支持通过键来访问值
print(dict1["name"])#通过键来访问值
#字典的应用=>字典可以用来存储一组相关的数据，例如一个学生的姓名、学号和成绩，可以用一个字典来表示
student={"name":"Bob","id":"12345","score":90}  
print(student)
#字典的常用方法=>keys()方法可以返回字典中的所有键，values()方法可以返回字典中的所有值，items()方法可以返回字典中的所有键值对
print(student.keys())#返回字典中的所有键
print(student.values())#返回字典中的所有值
print(student.items())#返回字典中的所有键值对
#字典的遍历=>for循环可以遍历字典中的每个键值对
for key,value in student.items():
    print(f"{key}:{value}") 
#集合的概念=>集合是一种无序不重复的元素集合，使用花括号{}定义
set1={1,2,3,4,5}
print(set1)
#集合的特点=>集合中的元素不能重复，集合中的元素是无序的，集合支持集合运算
set2={4,5,6,7,8}
print(set1.union(set2))#集合的并集
print(set1.intersection(set2))#集合的交集
print(set1.difference(set2))#集合的差集
#集合的应用=>集合可以用来存储一组不重复的数据，例如一个班级的学生名单，可以用一个集合来表示
class_students={"Alice","Bob","Charlie","David"}
print(class_students)
#集合的常用方法=>add()方法可以向集合中添加一个元素，remove()方法可以从集合中删除一个元素，clear()方法可以清空集合
class_students.add("Eve")
print(class_students)
class_students.remove("Alice")
print(class_students)
class_students.clear()
print(class_students)
#集合的遍历=>for循环可以遍历集合中的每个元素
set3={"apple","banana","orange"}
for fruit in set3:
    print(fruit)
#循环的概念=>循环是一种重复执行某段代码的结构，常见的循环有for循环和while循环
#for循环的语法=>for 变量 in 可迭代对象: 循环体
#for循环的应用=>for循环可以用来遍历列表、元组、字典和集合等可迭代对象
list5=[1,2,3,4,5]
for num in list5:
    print(num)
dict2={"name":"Alice","age":30,"gender":"男"}
for key,value in dict2.items():
    print(f"{key}:{value}")
#嵌套循环=>嵌套循环是指在一个循环体内又包含一个循环，可以用来处理多维数据结构
matrix=[[1,2,3],[4,5,6],[7,8,9]]
for row in matrix:
    for num in row:
        print(num)
#while循环的语法=>while 条件: 循环体
#while循环的应用=>while循环可以用来实现一些需要重复执行的操作，例如计算阶乘、求最大公约数等
#计算阶乘
# num=int(input("请输入一个整数："))
# factorial=1
# i=1
# while i<=num:
#     factorial*=i
#     i+=1
# print(f"{num}的阶乘是{factorial}")
#求最大公约数
# a=int(input("请输入第一个整数："))
# b=int(input("请输入第二个整数："))
# while b!=0:
#     a,b=b,a%b
# print(f"最大公约数是{a}")
#循环的控制语句=>break语句可以跳出当前循环，continue语句可以跳过当前循环的剩余部分，进入下一次循环
#使用break语句
for num in range(1,10):
    if num==5:
        break
    print(num)
#使用continue语句
for num in range(1,10):
    if num==5:
        continue
    print(num)
#循环的嵌套和控制=>在嵌套循环中，break语句只能跳出当前所在的循环，continue语句只能跳过当前所在的循环的剩余部分
for i in range(1,4):
    for j in range(1,4):
        if i==2 and j==2:
            break
        print(f"i={i},j={j}")
#使用continue语句
for i in range(1,4):
    for j in range(1,4):
        if i==2 and j==2:
            continue
        print(f"i={i},j={j}")
#文件的概念=>文件是一种存储数据的媒介，可以是文本文件、二进制文件等
#文件的操作=>可以使用open()函数打开一个文件，使用read()方法读取文件内容，使用write()方法写入文件内容，使用close()方法关闭文件
#打开文件
# file=open("example.txt","w")#以写入模式打开文件，如果文件不存在则创建
# #写入文件内容
# file.write("Hello,world!\n")
# file.write("This is a file example.\n")
# #关闭文件
# file.close()
# #读取文件内容
# file=open("example.txt","r")#以读取模式打开文件
# content=file.read()#读取文件内容
# print(content)
# #关闭文件
# file.close()
# #文件的应用=>文件可以用来存储和处理大量的数据，例如日志文件、配置文件等
# #写入日志文件
# log_file=open("log.txt","a")#以追加模式打开文件，如果文件不存在则创建
# log_file.write("2024-06-01 10:00:00 INFO: This is a log message.\n")
# log_file.close()
# #读取日志文件
# log_file=open("log.txt","r")#以读取模式打开文件
# log_content=log_file.read()#读取文件内容
# print(log_content)
# #文件的异常处理=>在文件操作过程中可能会发生一些异常，例如文件不存在、权限不足等，可以使用try-except语句来处理这些异常
# try:
#     file=open("nonexistent.txt","r")#尝试打开一个不存在的文件
#     content=file.read()#读取文件内容
#     print(content) 
# except FileNotFoundError:
#     print("文件不存在！")
# #使用with语句可以自动管理文件资源，无论是否发生异常，都会确保文件被正确关闭
# try:    
#     with open("example.txt","r") as file:#使用with语句打开文件
#         content=file.read()#读取文件内容
#         print(content)
# except FileNotFoundError:
#     print("文件不存在！")
# #文件的路径=>文件路径可以是绝对路径或相对路径，绝对路径是从根目录开始的完整路径，相对路径是相对于当前工作目录的路径
# #使用绝对路径打开文件
# file=open("C:/Users/username/Documents/example.txt","r")#使用绝对路径打开文件
# content=file.read()#读取文件内容
# print(content)
# file.close()
# #使用相对路径打开文件
# file=open("example.txt","r")#使用相对路径打开文件
# content=file.read()#读取文件内容
# print(content)
# #文件的操作模式=>open()函数的第二个参数可以指定文件的操作模式，常见的模式有"r"（读取）、"w"（写入）、"a"（追加）等
# #以写入模式打开文件
# file=open("example.txt","w")#以写入模式打开文件，如果文件不存在则创建
# file.write("This is a new content.\n")#写入文件内容
# file.close()
# #以追加模式打开文件
# file=open("example.txt","a")#以追加模式打开文件，如果文件不存在则创建
# file.write("This is an additional content.\n")#写入文件内容
# file.close()
# #以读取模式打开文件
# file=open("example.txt","r")#以读取模式打开文件
# content=file.read()#读取文件内容
# print(content)
# file.close()
# #文件的编码=>在处理文本文件时，可能会遇到编码问题，例如文件使用了不同的编码格式，可以使用open()函数的encoding参数来指定文件的编码
# #以指定编码打开文件
# file=open("example.txt","r",encoding="utf-8")#以指定编码打开文件
# content=file.read()#读取文件内容
# print(content)
# file.close()
#函数的概念=>函数是一段可以重复使用的代码块，可以接受输入参数并返回输出结果
#函数的定义=>使用def关键字定义一个函数，函数名后面跟着圆括号和冒号，函数体缩进编写
def greet(name):
    print(f"Hello, {name}!")
#函数的调用=>通过函数名和圆括号来调用一个函数，可以传递实参给函数
greet("Alice")
#函数的参数=>函数可以接受位置参数、默认参数、可变参数和关键字参数等不同类型的参数
#位置参数
def add(a,b):
    return a+b 
result=add(3,5)
print(result)
#默认参数
def greet(name="World"):
    print(f"Hello, {name}!")
greet()#使用默认参数
greet("Alice")#传递实参覆盖默认参数
#可变参数
def sum(*args):
    total=0
    for num in args:
        total+=num
    return total
result=sum(1,2,3,4,5)
print(result)
#关键字参数
def greet(name,age):
    print(f"Hello, {name}! You are {age} years old.")
    greet(name="Alice",age=30)#使用关键字参数传递实参
    greet(age=30,name="Alice")#关键字参数的顺序可以任意
#函数的返回值=>使用return语句可以从函数中返回一个值，函数执行到return语句时会立即结束并返回指定的值
def add(a,b):
    return a+b
result=add(3,5)
print(result)
#函数的递归=>递归是指一个函数调用自身，可以用来解决一些问题，例如计算阶乘、斐波那契数列等
#计算阶乘的递归函数
def factorial(n):
    if n==0:
        return 1
    else:
        return n*factorial(n-1)
result=factorial(5)
print(result)
#计算斐波那契数列的递归函数
def fibonacci(n):
    if n==0:
        return 0
    elif n==1:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)
result=fibonacci(10)
print(result)
#函数的匿名函数=>匿名函数是指没有名字的函数，可以使用lambda关键字来定义一个匿名函数
#定义一个匿名函数来计算两个数的和
add=lambda a,b:a+b
result=add(3,5)
print(result)
#定义一个匿名函数来计算一个数的平方
square=lambda x:x**2
result=square(5)
print(result)
#匿名函数的应用=>匿名函数可以用来作为一些函数的参数，例如map()函数、filter()函数等
#使用匿名函数和map()函数来计算一个列表中每个元素的平方
numbers=[1,2,3,4,5]
squared_numbers=list(map(lambda x:x**2,numbers))
print(squared_numbers)
#使用匿名函数和filter()函数来过滤一个列表中大于3的元素
numbers=[1,2,3,4,5]
filtered_numbers=list(filter(lambda x:x>3,numbers))
print(filtered_numbers)
#函数的作用域=>函数内部定义的变量具有局部作用域，只能在函数内部访问，函数外部定义的变量具有全局作用域，可以在函数内部和外部访问
#局部变量
def greet():
    name="Alice" #局部变量
    print(f"Hello, {name}!")
greet()
#全局变量
name="Bob" #全局变量
def greet():
    print(f"Hello, {name}!")
greet()
#函数的嵌套和闭包=>在一个函数内部定义另一个函数，内部函数可以访问外部函数的变量，这种结构称为闭包
def outer():
    message="Hello, World!" #外部函数的变量
    def inner():
        print(message) #内部函数访问外部函数的变量
    return inner
greet=outer() #调用外部函数，返回内部函数
greet() #调用内部函数，输出"Hello, World!"
#函数的装饰器=>装饰器是一种特殊的函数，可以用来修改另一个函数的行为，使用@符号来应用装饰器
def decorator(func):
    def wrapper():
        print("Before calling the function.")
        func()
        print("After calling the function.")
    return wrapper
@decorator
def greet():
    print("Hello, World!")
#调用装饰后的函数
greet()
#函数的递归和尾递归优化=>递归函数在某些情况下可能会导致栈溢出，可以使用尾递归优化来避免这个问题
def factorial(n,acc=1):
    if n==0:
        return acc
    else:
        return factorial(n-1,n*acc)
result=factorial(5)
print(result)
#函数的参数传递=>函数的参数传递方式有值传递和引用传递两种，Python中的参数传递方式是基于对象的引用传递
def modify_list(lst):
    lst.append(4) #修改列表对象
my_list=[1,2,3]
modify_list(my_list)
print(my_list)
#函数的递归和迭代=>递归和迭代是两种解决问题的方法，递归是通过函数调用自身来解决问题，迭代是通过循环来解决问题
#递归实现阶乘
def factorial(n):
    if n==0:
        return 1
    else:
        return n*factorial(n-1)
result=factorial(5)
print(result)
#迭代实现阶乘
def factorial(n):
    result=1
    for i in range(1,n+1):
        result*=i
    return result
result=factorial(5)
print(result)
#函数的递归和迭代的性能比较=>在某些情况下，递归可能会比迭代更简洁和易读，但在性能方面，迭代通常比递归更高效，因为递归会涉及到函数调用的开销
import time
def recursive_factorial(n):
    if n==0:
        return 1
    else:
        return n*recursive_factorial(n-1)
def iterative_factorial(n):
    result=1
    for i in range(1,n+1):
        result*=i
    return result
n=5
start_time=time.time()
recursive_result=recursive_factorial(n)
end_time=time.time()
print(f"递归阶乘结果：{recursive_result},耗时：{end_time-start_time}秒")
start_time=time.time()
iterative_result=iterative_factorial(n)
end_time=time.time()
print(f"迭代阶乘结果：{iterative_result},耗时：{end_time-start_time}秒")
#global关键字=>global关键字可以在函数内部声明一个变量为全局变量，使得该变量在函数内部和外部都可以访问和修改
def modify_global():
    global count #声明count为全局变量
    count+=1 #修改全局变量
count=0 #全局变量
print(count) #输出0
modify_global() #调用函数修改全局变量
print(count) #输出1
#nonlocal关键字=>nonlocal关键字可以在嵌套函数中声明一个变量为非局部变量，使得该变量在内部函数中可以访问和修改外部函数的变量
def outer():
    count=0 #外部函数的变量
    def inner():
        nonlocal count #声明count为非局部变量
        count+=1 #修改外部函数的变量
        print(count) #输出修改后的值
    return inner
#调用外部函数，返回内部函数
counter=outer()
counter() #调用内部函数，输出1
counter() #调用内部函数，输出2
#函数的参数传递和可变对象=>在Python中，函数的参数传递方式是基于对象的引用传递，对于可变对象（如列表、字典等），在函数内部修改对象会影响到外部的对象
def modify_list(lst):
    lst.append(4) #修改列表对象
my_list=[1,2,3]
modify_list(my_list)
print(my_list) #输出[1, 2, 3, 4]
#闭包和装饰器的应用=>闭包和装饰器可以用来实现一些高级的功能，例如缓存函数结果、计时函数执行时间等
#使用闭包实现函数结果缓存
def cache(func):
    cached_results={}
    def wrapper(*args):
        if args in cached_results:
            return cached_results[args] #返回缓存的结果
        else:
            result=func(*args) #调用原函数计算结果
            cached_results[args]=result #将结果缓存起来
            return result
    return wrapper
@cache
def fibonacci(n):
    if n==0:
        return 0
    elif n==1:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)
result=fibonacci(10)
print(result)
#面向对象编程=>面向对象编程是一种编程范式，使用类和对象来组织代码，可以实现封装、继承和多态等特性
#类的定义=>使用class关键字定义一个类，类名通常使用大写字母开头，类体缩进编写
class Person:
    def __init__(self,name,age):
        self.name=name #实例属性
        self.age=age #实例属性
    def greet(self):
        print(f"Hello, my name is {self.name} and I am {self.age} years old.") #实例方法
#创建对象
person1=Person("Alice",30)
person2=Person("Bob",25)
#调用对象的方法
person1.greet()
person2.greet()
#类的继承=>使用class关键字定义一个子类，子类可以继承父类的属性和方法，并且可以添加自己的属性和方法
class Student(Person):
    def __init__(self,name,age,student_id):
        super().__init__(name,age) #调用父类的构造方法
        self.student_id=student_id #子类的属性
    def study(self):
        print(f"{self.name} is studying.") #子类的方法
#创建子类对象
student1=Student("Charlie",20,"12345")
student2=Student("David",22,"67890")
#调用子类的方法
student1.greet() #调用父类的方法
student1.study() #调用子类的方法
student2.greet() #调用父类的方法
student2.study() #调用子类的方法
#类的多态=>多态是指不同类的对象可以通过相同的接口来调用方法，Python中的多态是通过鸭子类型实现的
class Animal:
    def speak(self):
        pass
class Dog(Animal):
    def speak(self):
        print("Woof!")
class Cat(Animal):
    def speak(self):
        print("Meow!")
def make_animal_speak(animal):
    animal.speak() #调用动物的speak方法
dog=Dog()
cat=Cat()
make_animal_speak(dog) #输出"Woof!"
make_animal_speak(cat) #输出"Meow!"
#类的封装=>封装是指将数据和操作数据的方法绑定在一起，并且隐藏内部的实现细节，Python中的封装是通过访问控制来实现的
#os模块的封装
import os
#获取当前工作目录
current_directory=os.getcwd()
print(current_directory)
#创建一个新目录
new_directory=os.path.join(current_directory,"new_folder")
os.makedirs(new_directory, exist_ok=True)
print(new_directory)
#删除目录
os.rmdir(new_directory)
print(f"{new_directory} has been removed.")
