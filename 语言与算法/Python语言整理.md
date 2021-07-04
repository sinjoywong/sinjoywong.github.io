# 命名空间和作用域

变量是拥有匹配对象的名字（标识符）。命名空间是一个包含了变量名称们（键）和它们各自相应的对象们（值）的字典。

一个 Python 表达式可以访问局部命名空间和全局命名空间里的变量。如果一个局部变量和一个全局变量重名，则局部变量会覆盖全局变量。

每个函数都有自己的命名空间。类的方法的作用域规则和通常函数的一样。

Python 会智能地猜测一个变量是局部的还是全局的，**它假设任何在函数内赋值的变量都是局部的。**

因此，如果要给函数内的全局变量赋值，必须使用 global 语句。

global VarName 的表达式会告诉 Python， VarName 是一个全局变量，这样 Python 就不会在局部命名空间里寻找这个变量了。

例如，我们在全局命名空间里定义一个变量 Money。我们再在函数内给变量 Money 赋值，然后 Python 会假定 Money 是一个局部变量。然而，我们并没有在访问前声明一个局部变量 Money，结果就是会出现一个 UnboundLocalError 的错误。取消 global 语句前的注释符就能解决这个问题。

```python
#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
Money = 2000
def AddMoney():
   # 想改正代码就取消以下注释:
   # global Money
   Money = Money + 1
 
print Money
AddMoney()
print Money
```



# 类的实例创建

## `__new__`方法

初始化一个类,第一个调用的方法.

## `__init__`方法

初始化一个类对象,在`__new__`方法之后调用的初始化方法.

实例:

```python
class Person(object):
    """Silly Person"""
 
    def __new__(cls, name, age):
        print '__new__ called.'
        return super(Person, cls).__new__(cls, name, age)
 
    def __init__(self, name, age):
        print '__init__ called.'
        self.name = name
        self.age = age
 
    def __str__(self):
        return '<Person: %s(%s)>' % (self.name, self.age)
 
if __name__ == '__main__':
    piglei = Person('wuhuang', 100)
    print piglei
```

执行结果:

```Python
__new__ called.
__init__ called.
<Person: piglei(24)>
```

1.p = Person(name, age)
2.首先执行使用name和age参数来执行Person类的**new**方法，这个**new**方法会 返回Person类的一个实例（通常情况下是使用 super(Persion, cls).**new**(cls, … …) 这样的方式），
3.然后利用这个实例来调用类的**init**方法，上一步里面**new**产生的实例也就是 **init**里面的的 self
所以，**init** 和 **new** 最主要的区别在于：
1.**init** 通常用于初始化一个新实例，控制这个初始化的过程，比如添加一些属性， 做一些额外的操作，发生在类实例被创建完以后。它是实例级别的方法。
2.**new** 通常用于控制生成一个新实例的过程。它是类级别的方法。
但是说了这么多，**new**最通常的用法是什么呢，我们什么时候需要**new**？

依照Python官方文档的说法，**new**方法主要是当你继承一些不可变的class时(比如int, str, tuple)， 提供给你一个自定义这些类的实例化过程的途径。还有就是实现自定义的metaclass。
首先我们来看一下第一个功能，具体我们可以用int来作为一个例子：
假如我们需要一个永远都是正数的整数类型，通过集成int，我们可能会写出这样的代码。

```python
def __init__(self, value):
   super(PositiveInteger, self).__init__(self, abs(value))
 
i = PositiveInteger(-3)
print i
```

但运行后会发现，结果根本不是我们想的那样，我们任然得到了-3。这是因为对于int这种 不可变的对象，我们只有重载它的**new**方法才能起到自定义的作用。
这是修改后的代码：

```python
def __new__(cls, value):
    return super(PositiveInteger, cls).__new__(cls, abs(value))

i = PositiveInteger(-3)
print i
```

通过重载**new**方法，我们实现了需要的功能。
另外一个作用，关于自定义metaclass。其实我最早接触**new**的时候，就是因为需要自定义 metaclass，但鉴于篇幅原因，我们下次再来讲python中的metaclass和**new**的关系。

## 用new来实现单例

事实上，当我们理解了**new**方法后，我们还可以利用它来做一些其他有趣的事情，比如实现 设计模式中的 单例模式(singleton) 。
因为类每一次实例化后产生的过程都是通过**new**来控制的，所以通过重载**new**方法，我们 可以很简单的实现单例模式。

```python
def __new__(cls):
        # 关键在于这，每一次实例化的时候，我们都只会返回这同一个instance对象
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance
 
obj1 = Singleton()
obj2 = Singleton()
 
obj1.attr1 = 'value1'
print obj1.attr1, obj2.attr1
print obj1 is obj2
```

输出结果：

```php
True
```

可以看到obj1和obj2是同一个实例。



# object类



# self属性



# attr属性

## hasattr

hasattr() 函数用来判断某个类实例对象是否包含指定名称的属性或方法。该函数的语法格式如下：

hasattr(obj, name).

示例:

```Python
class Demo:
    def __init__ (self):
        self.name = "wang"
    def say(self):
        print("helloworld")

demo = Demo()
print(hasattr(demo,"name"))
print(hasattr(demo,"say"))
```

程序输出结果为：

```
True
True
True
```

## getattr

getattr()函数用于获取某个类实例对象中指定属性的值.和 hasattr() 函数不同，该函数只会从类对象包含的所有属性中进行查找。

getattr() 函数的语法格式如下：

`getattr(obj, name[, default])`

其中，obj 表示指定的类实例对象，name 表示指定的属性名，而 default 是可选参数，用于设定该函数的默认返回值，即当函数查找失败时，如果不指定 default 参数，则程序将直接报 AttributeError 错误，反之该函数将返回 default 指定的值。

```python
class Demo:
    def __init__ (self):
        self.name = "wang"
    def say(self):
        print("helloworld")

demo = Demo()
print(getattr(demo,"name"))
print(getattr(demo,"say"))
print(getattr(demo,"run",'this is default return value when search failed'))
#print(getattr(demo,"run"))
```

输出结果:

```python
wang
<bound method Demo.say of <__main__.Demo object at 0x1059151c0>>
this is default return value when search faile
```

当把上面的最后一句放开后, 则直接返回错误:

```python
   print(getattr(demo,"run"))
AttributeError: 'Demo' object has no attribute 'run'
```

可以看到，对于类中已有的属性，getattr() 会返回它们的值，而如果该名称为方法名，则返回该方法的状态信息；反之，如果该明白不为类对象所有，要么返回默认的参数，要么程序报 AttributeError 错误。

## setattr

setattr() 函数的功能相对比较复杂，它最基础的功能是修改类实例对象中的属性值。其次，它还可以实现为实例对象动态添加属性或者方法。

`setattr()` 函数的语法格式如下：

`setattr(obj, name, value)`

### 修改实例对象的属性值

```python
class Demo:
    def __init__ (self):
        self.name = "wang"
    def say(self):
        print("helloworld")
demo = Demo()
print(getattr(demo,"name"))
setattr(demo,"name","li")
print(getattr(demo,"name")
```

结果:

```Python
wang
li
```

修改类属性为一个类方法, 或将一个类方法修改为类属性

```Python
class Demo:
    def __init__ (self):
        self.name = "wang"
    def say(self):
        print("helloworld")

def walk(self):
    print("I am walking")

demo = Demo()

setattr(demo,"name",walk)
print(getattr(demo,"name"))
demo.name(demo)
```

结果:

```Python
<function walk at 0x1039f85e0>
I am walking
```

# super

**super()** 函数是用于调用父类(超类)的一个方法。

super 是用来解决多重继承问题的，直接用类名调用父类方法在使用单继承的时候没问题，但是如果使用多继承，会涉及到查找顺序（MRO）、重复调用（钻石继承）等种种问题。

MRO 就是类的方法解析顺序表, 其实也就是继承父类方法时的顺序表。

### 语法

以下是 super() 方法的语法:

```
super(type[, object-or-type])
```

### 参数

- type -- 类。
- object-or-type -- 类，一般是 self

```python
#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
class FooParent(object):
    def __init__(self):
        self.parent = 'I\'m the parent.'
        print ('Parent')
    
    def bar(self,message):
        print ("%s from Parent" % message)
 
class FooChild(FooParent): #类FooChild集成了FooParent
    def __init__(self):
        # super(FooChild,self) 首先找到 FooChild 的父类（就是类 FooParent），然后把类 FooChild 的对象转换为类 FooParent 的对象
        super(FooChild,self).__init__()    
        print ('Child')
        
    def bar(self,message):
        super(FooChild, self).bar(message)
        print ('Child bar fuction')
        print (self.parent)
 
if __name__ == '__main__':
    fooChild = FooChild()
    fooChild.bar('HelloWorld')
```

执行结果:

```Python
Parent
Child
HelloWorld from Parent
Child bar fuction
I'm the parent.
```

# classmethod修饰符

**classmethod** 修饰符对应的函数不需要实例化，不需要 self 参数，但第一个参数需要是表示自身类的 cls 参数，可以来调用类的属性，类的方法，实例化对象等。

```python
#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
class A(object):
    bar = 1
    def func1(self):  
        print ('foo') 
    @classmethod
    def func2(cls):
        print ('func2')
        print (cls.bar)
        cls().func1()   # 调用 foo 方法
 
A.func2()               # 不需要实例化
```

输出结果为：

```shell
func2
1
foo
```



```python
class A(object):
    # 属性默认为类属性（可以给直接被类本身调用）
    num = "类属性"

    # 实例化方法（必须实例化类之后才能被调用）
    def func1(self): # self : 表示实例化类后的地址id
        print("func1")
        print(self)

    # 类方法（不需要实例化类就可以被类本身调用）
    @classmethod
    def func2(cls):  # cls : 表示没用被实例化的类本身
        print("func2")
        print(cls)
        print(cls.num)
        cls().func1()

    # 不传递传递默认self参数的方法（该方法也是可以直接被类调用的，但是这样做不标准）
    def func3():
        print("func3")
        print(A.num) # 属性是可以直接用类本身调用的
    
# A.func1() 这样调用是会报错：因为func1()调用时需要默认传递实例化类后的地址id参数，如果不实例化类是无法调用的
A.func2()
A.func3()
```



# ____slots__

Python允许在定义class的时候，定义一个特殊的`__slots__`变量，来限制该class能添加的属性。例如：当定义一个class 后，想要限制它的属性时，我们可以用 __slots__ 添加 age 、name、color 属性，再调用。

```python
class dog():
    __slots__ =  'age','color','name'
    def __init__(self,age,name,color):
        self.age = age
        self.name = name
        self.color=color
    def get_info(self):
        for item in dir(self):
            if isinstance(item, (str,int)):
                print (item)
    def some_info(self):
        print ( self.age,self.name,self.color)
 
 
emma = dog(1 , 'Emma' , 'red')
nasa = dog(2 , 'Nasa' , 'black')
#emma.get_info()
emma.some_info()
nasa.some_info()
```

若__slots_ 只给出age、name属性时，这时候再绑定color属性则会报错。

```python
class dog():
    __slots__ =  'age','name'
    def __init__(self,age,name,color):
        self.age = age
        self.name = name
        self.color=color
    def get_info(self):
        for item in dir(self):
            if isinstance(item, (str,int)):
                print (item)
    def some_info(self):
        print ( self.age,self.name,self.color)
 
 
emma = dog(1 , 'Emma' , 'red')
nasa = dog(2 , 'Nasa' , 'black')
#emma.get_info()
emma.some_info()
nasa.some_info()
 
 
#结果输出
AttributeError: 'dog' object has no attribute 'color'

```

# cls与self

The distinction between `"self"` and `"cls"` is defined in `PEP 8` . As Adrien said, this is not a mandatory. It's a coding style. `PEP 8` says:

> *Function and method arguments*:
> Always use `self` for the first argument to instance methods.
> Always use `cls` for the first argument to class methods.

# shell常用

`'bash {0}'.format(setup_rgw_script)`: 将script作为shell的脚本名称输入.



#  main(sys.argv[1:]

sys.argv[]说白了就是一个从程序外部获取参数的桥梁，这个“外部”很关键，所以那些试图从代码来说明它作用的解释一直没看明白。因为我们从外部取得的参数可以是多个，所以获得的是一个列表（list)，也就是说sys.argv其实可以看作是一个列表，所以才能用[]提取其中的元素。其第一个元素是程序本身，随后才依次是外部给予的参数。

sys.argv[0] 这就是0指代码（即此.py程序）本身的意思

而sys.argv[1:]则表示一个列表,从第一个开始.



