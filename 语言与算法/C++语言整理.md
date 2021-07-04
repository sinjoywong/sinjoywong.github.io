C++

1. overide作用:在派生类中提醒自己要重写这个同参数函数,不写则报错

定义一个函数为虚函数，不代表函数为不被实现的函数。

定义他为虚函数是为了允许用基类的指针来调用子类的这个函数。

定义一个函数为纯虚函数，才代表函数没有被实现。

定义纯虚函数是为了实现一个接口，起到一个规范的作用，规范继承这个类的程序员必须实现这个函数



它虚就虚在所谓"推迟联编"或者"动态联编"上，一个类函数的调用并不是在编译时刻被确定的，而是在运行时刻被确定的。由于编写代码的时候并不能确定被调用的是基类的函数还是哪个派生类的函数，所以被成为"虚"函数。

**虚函数只能借助于指针或者引用来达到多态的效果**



纯虚函数是在基类中声明的虚函数，它在基类中没有定义，但要求任何派生类都要定义自己的实现方法。在基类中实现纯虚函数的方法是在函数原型后加 **=0**:

```
virtual void funtion1()=0
```

**二、引入原因**

　　

1、为了方便使用多态特性，我们常常需要在基类中定义虚拟函数。

　　

2、在很多情况下，基类本身生成对象是不合情理的。例如，动物作为一个基类可以派生出老虎、孔雀等子类，但动物本身生成对象明显不合常理。

　　

为了解决上述问题，引入了纯虚函数的概念，将函数定义为纯虚函数（方法：**virtual ReturnType Function()= 0;**），则编译器要求在派生类中必须予以重写以实现多态性。同时含有纯虚拟函数的类称为抽象类，它不能生成对象。这样就很好地解决了上述两个问题。

声明了纯虚函数的类是一个抽象类。所以，用户不能创建类的实例，只能创建它的派生类的实例。

**纯虚函数最显著的特征是**：它们必须在继承类中重新声明函数（不要后面的＝0，否则该派生类也不能实例化），而且它们在抽象类中往往没有定义。

定义纯虚函数的目的在于，使派生类仅仅只是继承函数的接口。

纯虚函数的意义，让所有的类对象（主要是派生类对象）都可以执行纯虚函数的动作，但类无法为纯虚函数提供一个合理的默认实现。所以类纯虚函数的声明就是在告诉子类的设计者，"你必须提供一个纯虚函数的实现，但我不知道你会怎样实现它"。



## 抽象类的介绍

抽象类是一种特殊的类，它是为了抽象和设计的目的为建立的，它处于继承层次结构的较上层。

**（1）抽象类的定义：** 称带有纯虚函数的类为抽象类。

**（2）抽象类的作用：** 抽象类的主要作用是将有关的操作作为结果接口组织在一个继承层次结构中，由它来为派生类提供一个公共的根，派生类将具体实现在其基类中作为接口的操作。所以派生类实际上刻画了一组子类的操作接口的通用语义，这些语义也传给子类，子类可以具体实现这些语义，也可以再将这些语义传给自己的子类。

**（3）使用抽象类时注意：**

- 抽象类只能作为基类来使用，其纯虚函数的实现由派生类给出。如果派生类中没有重新定义纯虚函数，而只是继承基类的纯虚函数，则这个派生类仍然还是一个抽象类。如果派生类中给出了基类纯虚函数的实现，则该派生类就不再是抽象类了，它是一个可以建立对象的具体的类。
- 抽象类是不能定义对象的。

## 总结：

- 1、纯虚函数声明如下： **virtual void funtion1()=0;** 纯虚函数一定没有定义，纯虚函数用来规范派生类的行为，即接口。包含纯虚函数的类是抽象类，抽象类不能定义实例，但可以声明指向实现该抽象类的具体类的指针或引用。

- 2、虚函数声明如下：**virtual ReturnType FunctionName(Parameter)** 虚函数必须实现，如果不实现，编译器将报错，错误提示为：

  ```
  error LNK****: unresolved external symbol "public: virtual void __thiscall ClassName::virtualFunctionName(void)"
  ```

- 3、对于虚函数来说，父类和子类都有各自的版本。由多态方式调用的时候动态绑定。

- 4、实现了纯虚函数的子类，该纯虚函数在子类中就编程了虚函数，子类的子类即孙子类可以覆盖该虚函数，由多态方式调用的时候动态绑定。

- 5、虚函数是C++中用于实现多态(polymorphism)的机制。核心理念就是通过基类访问派生类定义的函数。

- 6、在有动态分配堆上内存的时候，析构函数必须是虚函数，但没有必要是纯虚的。

- 7、友元不是成员函数，只有成员函数才可以是虚拟的，因此友元不能是虚拟函数。但可以通过让友元函数调用虚拟成员函数来解决友元的虚拟问题。

- 8、析构函数应当是虚函数，将调用相应对象类型的析构函数，因此，如果指针指向的是子类对象，将调用子类的析构函数，然后自动调用基类的析构函数。

有纯虚函数的类是抽象类，不能生成对象，只能派生。他派生的类的纯虚函数没有被改写，那么，它的派生类还是个抽象类。

定义纯虚函数就是为了让基类不可实例化化，因为实例化这样的抽象数据结构本身并没有意义，或者给出实现也没有意义。

实际上我个人认为纯虚函数的引入，是出于两个目的：

- 1、为了安全，因为避免任何需要明确但是因为不小心而导致的未知的结果，提醒子类去做应做的实现。
- 2、为了效率，不是程序执行的效率，而是为了编码的效率。

> 

多态（polymorphism）是面向对象编程语言的一大特点，而虚函数是实现多态的机制。其核心理念就是通过基类访问派生类定义的函数。多态性使得程序调用的函数是在运行时动态确定的，而不是在编译时静态确定的。使用一个基类类型的指针或者引用，来指向子类对象，进而调用由子类复写的个性化的虚函数，这是C++实现多态性的一个最经典的场景。

- 虚函数，在类成员方法的声明（不是定义）语句前加“virtual”, 如 virtual void func()
- 纯虚函数，在虚函数后加“=0”，如 virtual void func()=0
- 对于虚函数，子类可以（也可以不）重新定义基类的虚函数，该行为称之为复写Override。
- 对于纯虚函数，子类必须提供纯虚函数的个性化实现。

在派生子类中对虚函数和纯虚函数的个性化实现，都体现了“多态”特性。但区别是：

- 子类如果不提供虚函数的实现，将会自动调用基类的缺省虚函数实现，作为备选方案；
- 子类如果不提供纯虚函数的实现，编译将会失败。尽管在基类中可以给出纯虚函数的实现，但无法通过指向子类对象的基类类型指针来调用该纯虚函数，也即不能作为子类相应纯虚函数的备选方案。（纯虚函数在基类中的实现跟多态性无关，它只是提供了一种语法上的便利，在变化多端的应用场景中留有后路。）

https://zhuanlan.zhihu.com/p/37331092





# 友元类

**Friend Class** A friend class can access private and protected members of other class in which it is declared as friend. It is sometimes useful to allow a particular class to access private members of other class. For example a LinkedList class may be allowed to access private members of Node.

```c++
class Node { 
private: 
    int key; 
    Node* next; 
    /* Other members of Node Class */
  
    // Now class  LinkedList can 
    // access private members of Node 
    friend class LinkedList; 
}; 
```



# std::set:

```c++
std::set<string> allowed_origins(trusted_cors_origins.begin(),trusted_cors_origins.end());


```

# std::unique_ptr:



# std::shared_ptr:

std::shared_ptr大概总结有以下几点:

(1) 智能指针主要的用途就是方便资源的管理，**自动释放没有指针引用的资源**。

(2) 使用**引用计数**来标识是否有多余指针指向该资源。(注意，shart_ptr本身指针会占1个引用)

(3) 在**赋值操作**中, 原来资源的引用计数会减一，新指向的资源引用计数会加一。

   std::shared_ptr<Test> p1(new Test);

   std::shared_ptr<Test> p2(new Test);

   p1 = p2;

(4) **引用计数加一/减一操作是原子性的**，所以线程安全的。

(5) make_shared要优于使用new，**make_shared可以一次将需要内存分配好**。

```
std::shared_ptr<Test> p = std::make_shared<Test>();
std::shared_ptr<Test> p(new Test);
```

(6) std::shared_ptr的大小**是原始指针的两倍**，因为它的内部有一个原始指针指向资源，同时有个指针指向引用计数。

(7) **引用计数是分配在动态分配的**，std::shared_ptr支持拷贝，新的指针获可以获取前引用计数个数。

```c++
include <iostream>
#include <memory>
#include <thread>
#include <chrono>
#include <mutex>

struct Test {
    Test() { std::cout << "  Test::Test()\n"; }
    ~Test() { std::cout << "  Test::~Test()\n"; }
};

//线程函数
void thr(std::shared_ptr<Test> p){
    //线程暂停1s
    std::this_thread::sleep_for(std::chrono::seconds(1));

    //赋值操作, shared_ptr引用计数use_cont加1(c++11中是原子操作)
    std::shared_ptr<Test> lp = p;
    {
        //static变量(单例模式),多线程同步用
        static std::mutex io_mutex;

        //std::lock_guard加锁
        std::lock_guard<std::mutex> lk(io_mutex);
        std::cout << "local pointer in a thread:\n"
                  << "  lp.get() = " << lp.get()
                  << ", lp.use_count() = " << lp.use_count() << '\n';
    }
}

int main() {
    //使用make_shared一次分配好需要内存
    std::shared_ptr<Test> p = std::make_shared<Test>();
    //std::shared_ptr<Test> p(new Test);

    std::cout << "Created a shared Test\n"
              << "  p.get() = " << p.get()
              << ", p.use_count() = " << p.use_count() << '\n';

    //创建三个线程,t1,t2,t3
    //形参作为拷贝, 引用计数也会加1
    std::thread t1(thr, p), t2(thr, p), t3(thr, p);
    std::cout << "Shared ownership between 3 threads and released\n"
              << "ownership from main:\n"
              << "  p.get() = " << p.get()
              << ", p.use_count() = " << p.use_count() << '\n';
    //等待结束
    t1.join(); t2.join(); t3.join();
    std::cout << "All threads completed, the last one deleted\n";

    return 0;
}
```

# 强引用与弱引用

## 强引用

当对象被创建时，计数为1；每创建一个变量引用该对象时，该对象的计数就增加1；当上述变量销毁时，对象的计数减1，当计数为0时，这个对象也就被析构了。

强引用计数在很多种情况下都是可以正常工作的，但是也有不凑效的时候，当出现循环引用时，就会出现严重的问题，以至于出现内存泄露，如下代码：

```c++
#include   
#include   
#include   
#include   
  
class parent;  
class children;  
  
typedef boost::shared_ptr parent_ptr;  
typedef boost::shared_ptr children_ptr;  
  
class parent  
{  
public:  
    ~parent() { std::cout <<"destroying parent\n"; }  
  
public:  
    children_ptr children;  
};  
  
class children  
{  
public:  
    ~children() { std::cout <<"destroying children\n"; }  
  
public:  
    parent_ptr parent;  
};  
  
void test()  
{  
    parent_ptr father(new parent());  
    children_ptr son(new children);  
  
    father->children = son;  
    son->parent = father;  
}  
  
void main()  
{  
    std::cout<<"begin test...\n";  
    test();  
    std::cout<<"end test.\n";  
}  
```

运行该程序可以看到，即使退出了test函数后，由于parent和children对象互相引用，它们的引用计数都是1，不能自动释放，并且此时这两个对象再无法访问到。这就引起了c++中那臭名昭著的内存泄漏。

一般来讲，解除这种循环引用有下面有三种可行的方法：

\1. 当只剩下最后一个引用的时候需要手动打破循环引用释放对象。 
\2. 当parent的生存期超过children的生存期的时候，children改为使用一个普通指针指向parent。 
\3. 使用弱引用的智能指针打破这种循环引用。 
虽然这三种方法都可行，但方法1和方法2都需要程序员手动控制，麻烦且容易出错。下面就介绍弱引用

**在多线程程序中，一个对象如果被多个线程访问，一般使用shared_ptr，通过引用计数来保证对象不被错误的释放导致其他线程访问出现问题。**

但这种引用计数解决不了循环引用的问题.

## 弱引用

boost::weak_ptr是boost提供的一个弱引用的智能指针，它的声明可以简化如下：

```c++
namespace boost {  
  
    template<</span>typename T> class weak_ptr {  
    public:  
        template <</span>typename Y>  
        weak_ptr(const shared_ptr& r);  
  
        weak_ptr(const weak_ptr& r);  
  
        ~weak_ptr();  
  
        T* get() const;   
        bool expired() const;   
        shared_ptr lock() const;  
    };   
}  
```

定义变量：

```c++
shared_ptr<T>  t(new T);weak_ptr<T> ptr(t); // t为一个T对象 //则当t被销毁时，ptr 被自动置为无效。使用方法如下： if ( shard_ptr<T> safePtr = ptr.lock() ) safePtr->Fun();
```

 可以看到，boost::weak_ptr必须从一个boost::share_ptr或另一个boost::weak_ptr转换而来，这也说明，进行该对象的内存管理的是那个强引用的boost::share_ptr。boost::weak_ptr只是提供了对管理对象的一个访问手段。boost::weak_ptr除了对所管理对象的基本访问功能（通过get()函数）外，还有两个常用的功能函数：expired()用于检测所管理的对象是否已经释放；lock()用于获取所管理的对象的强引用指针。

**由于弱引用不更改引用计数，类似普通指针，只要把循环引用的一方使用弱引用，即可解除循环引用。**对于上面的那个例子来说，只要把children的定义改为如下方式，即可解除循环引用：

```c++
class children  {  public:      ~children() { std::cout <<"destroying children\n"; }    public:      boost::weak_ptr parent;  };  
```

最后值得一提的是,虽然通过弱引用指针可以有效的解除循环引用，但这种方式必须在程序员能预见会出现循环引用的情况下才能使用，也可以是说 弱引用仅仅是一种编译期的解决方案，如果程序在运行过程中出现了循环引用，还是会造成内存泄漏的。因此，不要认为只要使用了智能指针便能杜绝内存泄漏。毕竟，对于C++来说，由于没有垃圾回收机制，内存泄漏对每一个程序员来说都是一个非常头痛的问题。

弱引用：它仅仅是对象 **存在时候的**引用，当对象不存在时弱引用能够检测到，从而避免非法访问，弱引用也不会修改对象的引用计数。这意味这弱引用它并不对对象的内存进行管理，在功能上类似于普通指针，然而一个比较大的区别是，弱引用能检测到所管理的对象是否已经被释放，从而避免访问非法内存。

# std::make_shared:

rgw_cors_rule_for_trusted_origins =
      std::make_shared<RGWCORSRule>(allowed_origins, allowed_hdrs, exposable_hdrs, allowed_methods, max_age);

```c++
shared_ptr<string> p1 = make_shared<string>(10, '9');  shared_ptr<string> p2 = make_shared<string>("hello");  shared_ptr<string> p3 = make_shared<string>(); 
```

**尽量使用make_shared初始化**

C++11 中引入了智能指针, 同时还有一个模板函数 std::make_shared 可以返回一个指定类型的 std::shared_ptr, 那与 std::shared_ptr 的构造函数相比它能给我们带来什么好处呢 ?

## make_shared初始化的优点

### 提高性能

shared_ptr 需要维护引用计数的信息：
强引用, 用来记录当前有多少个存活的 shared_ptrs 正持有该对象. 共享的对象会在最后一个强引用离开的时候销毁( 也可能释放).
弱引用, 用来记录当前有多少个正在观察该对象的 weak_ptrs. 当最后一个弱引用离开的时候, 共享的内部信息控制块会被销毁和释放 (共享的对象也会被释放, 如果还没有释放的话).
如果你通过使用原始的 new 表达式分配对象, 然后传递给 shared_ptr (也就是使用 shared_ptr 的构造函数) 的话, shared_ptr 的实现没有办法选择, 而只能单独的分配控制块:

![image-20210414102511350](.%E8%AF%AD%E8%A8%80%E6%95%B4%E7%90%86.assets/image-20210414102511350.png)

如果选择使用 make_shared 的话, 情况就会变成下面这样:

![image-20210414102517598](.%E8%AF%AD%E8%A8%80%E6%95%B4%E7%90%86.assets/image-20210414102517598.png)

std::make_shared（比起直接使用new）的一个特性是能提升效率。使用std::make_shared允许编译器产生更小，更快的代码，产生的代码使用更简洁的数据结构。考虑下面直接使用new的代码：

```c++
std::shared_ptr<Widget> spw(new Widget);
```

很明显这段代码需要分配内存，但是它实际上要分配两次。每个std::shared_ptr都指向一个控制块，控制块包含被指向对象的引用计数以及其他东西。这个控制块的内存是在std::shared_ptr的构造函数中分配的。因此直接使用new，需要一块内存分配给Widget，还要一块内存分配给控制块。

如果使用std::make_shared来替换:

```c++
auto spw = std::make_shared<Widget>();
```

一次分配就足够了。这是因为std::make_shared申请一个单独的内存块来同时存放Widget对象和控制块。这个优化减少了程序的静态大小，因为代码只包含一次内存分配的调用，并且这会加快代码的执行速度，因为内存只分配了一次。另外，使用std::make_shared消除了一些控制块需要记录的信息，这样潜在地减少了程序的总内存占用。

对std::make_shared的效率分析可以同样地应用在std::allocate_shared上，所以std::make_shared的性能优点也可以扩展到这个函数上。

### 异常安全

我们在调用processWidget的时候使用computePriority()，并且用new而不是std::make_shared：

```c++
processWidget(std::shared_ptr<Widget>(new Widget),  //潜在的资源泄露               computePriority());
```

就像注释指示的那样，上面的代码会导致new创造出来的Widget发生泄露。那么到底是怎么泄露的呢？调用代码和被调用函数都用到了std::shared_ptr，并且std::shared_ptr就是被设计来阻止资源泄露的。当最后一个指向这儿的std::shared_ptr消失时，它们会自动销毁它们指向的资源。如果每个人在每个地方都使用std::shared_ptr，那么这段代码是怎么导致资源泄露的呢？

答案和编译器的翻译有关，编译器把源代码翻译到目标代码，在运行期，函数的参数必须在函数被调用前被估值，所以在调用processWidget时，下面的事情肯定发生在processWidget能开始执行之前：

表达式“new Widget”必须被估值，也就是，一个Widget必须被创建在堆上。
std::shared_ptr（负责管理由new创建的指针）的构造函数必须被执行。
computePriority必须跑完。
编译器不需要必须产生这样顺序的代码。但“new Widget”必须在std::shared_ptr的构造函数被调用前执行，因为new的结构被用为构造函数的参数，但是computePriority可能在这两个调用前（后，或很奇怪地，中间）被执行。也就是，编译器可能产生出这样顺序的代码：

```c++
执行“new Widget”。执行computePriority。执行std::shared_ptr的构造函数。
```

如果这样的代码被产生出来，并且在运行期，computePriority产生了一个异常，则在第一步动态分配的Widget就会泄露了，因为它永远不会被存放到在第三步才开始管理它的std::shared_ptr中。

使用std::make_shared可以避免这样的问题。调用代码将看起来像这样：

```c++
processWidget(std::make_shared<Widget>(),       //没有资源泄露              computePriority());           
```

在运行期，不管std::make_shared或computePriority哪一个先被调用。如果std::make_shared先被调用，则在computePriority调用前，指向动态分配出来的Widget的原始指针能安全地被存放到被返回的std::shared_ptr中。如果computePriority之后产生一个异常，std::shared_ptr的析构函数将发现它持有的Widget需要被销毁。并且如果computePriority先被调用并产生一个异常，std::make_shared就不会被调用，因此这里就不需要考虑动态分配的Widget了。

如果使用std::unique_ptr和std::make_unique来替换std::shared_ptr和std::make_shared，事实上，会用到同样的理由。因此，使用std::make_unique代替new就和“使用std::make_shared来写出异常安全的代码”一样重要。

## 缺点

### 构造函数是保护或私有时,无法使用 make_shared

`make_shared` 虽好, 但也存在一些问题, 比如, 当我想要创建的对象没有公有的构造函数时, `make_shared` 就无法使用了, 当然我们可以使用一些小技巧来解决这个问题, 比如这里 [How do I call ::std::make_shared on a class with only protected or private constructors?](https://links.jianshu.com/go?to=http%3A%2F%2Fstackoverflow.com%2Fquestions%2F8147027%2Fhow-do-i-call-stdmake-shared-on-a-class-with-only-protected-or-private-const%3Frq%3D1)

### 对象的内存可能无法及时回收

`make_shared` 只分配一次内存, 这看起来很好. 减少了内存分配的开销. 问题来了, `weak_ptr` 会保持控制块(强引用, 以及弱引用的信息)的生命周期, 而因此连带着保持了对象分配的内存, 只有最后一个 `weak_ptr` 离开作用域时, 内存才会被释放. 原本强引用减为 0 时就可以释放的内存, 现在变为了强引用, 若引用都减为 0 时才能释放, 意外的延迟了内存释放的时间. 这对于内存要求高的场景来说, 是一个需要注意的问题.

作者：宋大壮
链接：https://www.jianshu.com/p/03eea8262c11
来源：简书
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。





# std::tie



# namespace

引入了**命名空间**这个概念，它可作为附加信息来区分不同库中相同名称的函数、类、变量等。使用了命名空间即定义了上下文。本质上，命名空间就是定义了一个范围。

## 不连续的命名空间

命名空间可以定义在几个不同的部分中，因此命名空间是由几个单独定义的部分组成的。一个命名空间的各个组成部分可以分散在多个文件中。

所以，如果命名空间中的某个组成部分需要请求定义在另一个文件中的名称，则仍然需要声明该名称。下面的命名空间定义可以是定义一个新的命名空间，也可以是为已有的命名空间增加新的元素：

```c++
namespace namespace_name {   // 代码声明}
```



## 嵌套的命名空间

```c++
namespace namespace_name1 {   // 代码声明   namespace namespace_name2 {      // 代码声明   }}
```

您可以通过使用 :: 运算符来访问嵌套的命名空间中的成员：

```c++
// 访问 namespace_name2 中的成员 using namespace namespace_name1::namespace_name2;  // 访问 namespace:name1 中的成员 using namespace namespace_name1;
```

在上面的语句中，如果使用的是 namespace_name1，那么在该范围内 namespace_name2 中的元素也是可用的，如下所示：

```c++
#include <iostream>using namespace std; // 第一个命名空间namespace first_space{   void func(){      cout << "Inside first_space" << endl;   }   // 第二个命名空间   namespace second_space{      void func(){         cout << "Inside second_space" << endl;      }   }}using namespace first_space::second_space;int main () {   // 调用第二个命名空间中的函数   func();   return 0;}
```

# std::move

std::move并不能移动任何东西，它唯一的功能是将一个左值强制转化为**右值引用**，继而可以通过右值引用使用该值，以用于移动语义。从实现上讲，std::move基本等同于一个类型转换：static_cast<T&&>(lvalue);

1. C++ 标准库使用比如vector::push_back 等这类函数时,会对参数的对象进行复制,连数据也会复制.这就会造成对象内存的额外创建, 本来原意是想把参数push_back进去就行了,通过std::move，可以避免不必要的拷贝操作。
2. std::move是将对象的状态或者所有权从一个对象转移到另一个对象，只是转移，没有内存的搬迁或者内存拷贝所以可以提高利用效率,改善性能.。
3. 对指针类型的标准库对象并不需要这么做.

```c++
//摘自https://zh.cppreference.com/w/cpp/utility/move#include <iostream>#include <utility>#include <vector>#include <string>int main() {    std::string str = "Hello";    std::vector<std::string> v;    //调用常规的拷贝构造函数，新建字符数组，拷贝数据    v.push_back(str);    std::cout << "After copy, str is \"" << str << "\"\n";    //调用移动构造函数，掏空str，掏空后，最好不要使用str    v.push_back(std::move(str));    std::cout << "After move, str is \"" << str << "\"\n";    std::cout << "The contents of the vector are \"" << v[0]                                         << "\", \"" << v[1] << "\"\n";}
```

输出:

```c++
After copy, str is "Hello"After move, str is ""The contents of the vector are "Hello", "Hello"
```



# [左值、左值引用、右值、右值引用](https://www.cnblogs.com/SZxiaochun/p/8017475.html)

## 1、左值和右值的概念

左值是可以放在赋值号左边可以被赋值的值；左值必须要在**内存中有实体**；

右值当在赋值号右边取出值赋给其他变量的值；右值**可以在内存也可以在CPU寄存器**。

 ==一个对象被用作右值时，使用的是它的内容(值)，被当作左值时，使用的是它的地址**。**==

## 2、引用

引用是C++语法做的优化，引用的本质还是靠指针来实现的。引用相当于变量的别名。

引用可以改变指针的指向，还可以改变指针所指向的值。

引用的基本规则：

1. 声明引用的时候必须初始化，且一旦绑定，不可把引用绑定到其他对象；即引用必须初始化，不能对引用重定义**；**
2. 对引用的一切操作，就相当于对原对象的操作。

## 3、左值引用和右值引用

1. 左值引用

左值引用的基本语法：type &引用名 = 左值表达式；

2. 右值引用

右值引用的基本语法type &&引用名 = 右值表达式；

右值引用在企业开发人员在代码优化方面会经常用到。

右值引用的“&&”中间不可以有空格。

# 类型强制转换

![image-20210414102528466](.%E8%AF%AD%E8%A8%80%E6%95%B4%E7%90%86.assets/image-20210414102528466.png)

从图中可以看出，派生类不仅有自己的方法和属性，同时它还包括从父类继承来的方法和属性。当我们从派生类向基类转换时，不管用传统的c语言还是c++转换方式都可以百分百转换成功。但是可怕是向下转换类型，也就是我们从基类向派生类转换，当我们采用传统的C语言和c++转换时，就会出现意想不到的情况，因为转换后派生类自己的方法和属性丢失了，一旦我们去调用派生类的方法和属性那就糟糕了，这就是对类继承关系和内存分配理解不清晰导致的。好在c++增加了static_cast和dynamic_cast运用于继承关系类间的强制转化

## static转换

````c++
static_cast< new_type >(expression)
````

备注**：**new_type**为目标数据类型，**expression**为原始数据类型变量或者表达式。

**static_cast**相当于传统的C语言里的强制转换，该运算符把expression转换为new_type类型，用来强迫隐式转换如non-const对象转为const对象，编译时检查，用于非多态的转换，可以转换指针及其他，**但没有运行时类型检查来保证转换的安全性**。它主要有如下几种用法：

①**用于类层次结构中基类（父类）和派生类（子类）之间指针或引用的转换**。 
进行**上行**转换（把派生类的指针或引用转换成基类表示）是**安全**的； 
进行**下行**转换（把基类指针或引用转换成派生类表示）时，由于没有动态类型检查，所以是**不安全**的。 
②**用于基本数据类型之间的转换，如把int转换成char，把int转换成enum**。 
③**把空指针转换成目标类型的空指针**。 
④**把任何类型的表达式转换成void类型**。 
注意：static_cast不能转换掉expression的const、volatile、或者__unaligned属性

基本类型数据转换举例如下:

```c++
char a = 'a';int b = static_cast<char>(a);//正确，将char型数据转换成int型数据double *c = new double;void *d = static_cast<void*>(c);//正确，将double指针转换成void指针int e = 10;const int f = static_cast<const int>(e);//正确，将int型数据转换成const int型数据const int g = 20;int *h = static_cast<int*>(&g);//编译错误，static_cast不能转换掉g的const属性
```

类上行和下行转换:

```c++
class Base{};class Derived : public Base{}Base* pB = new Base();if(Derived* pD = static_cast<Derived*>(pB)){}//下行转换是不安全的(坚决抵制这种方法)Derived* pD = new Derived();if(Base* pB = static_cast<Base*>(pD)){}//上行转换是安全的
```

## dynamic转换

**转换方式：** 

```c++
dynamic_cast< type\* >(e)   //type必须是一个类类型且必须是一个有效的指针 dynamic_cast< type& >(e)    //type必须是一个类类型且必须是一个左值 dynamic_cast< type&& >(e)   //type必须是一个类类型且必须是一个右值
```

**e的类型必须符合以下三个条件中的任何一个：** 
1、e的类型是目标类型type的公有派生类 
2、e的类型是目标type的共有基类 
3、e的类型就是目标type的类型。

如果一条dynamic_cast语句的转换目标是指针类型并且失败了，则结果为0。如果转换目标是引用类型并且失败了，则dynamic_cast运算符将抛出一个std::bad_cast异常(该异常定义在typeinfo标准库头文件中)。e也可以是一个空指针，结果是所需类型的空指针。

dynamic_cast主要用于类层次间的**上行转换**和**下行转换**，还可以用于**类之间的交叉转换**（cross cast）。

在类层次间进行**上行转换**时，dynamic_cast和static_cast的效果是一样的；在进行**下行转换**时，dynamic_cast具有**类型检查的功能**，比static_cast更安全。dynamic_cast是唯一无法由旧式语法执行的动作，也是唯一**可能耗费重大运行成本**的转型动作。

（1）指针类型 
举例，Base为包含至少一个虚函数的基类，Derived是Base的共有派生类，如果有一个指向Base的指针bp，我们可以在运行时将它转换成指向Derived的指针，代码如下：

```c++
if(Derived *dp = dynamic_cast<Derived *>(bp)){  //使用dp指向的Derived对象  }else{  //使用bp指向的Base对象  }
```

值得注意的是，在上述代码中，if语句中定义了dp，这样做的好处是可以在一个操作中同时完成类型转换和条件检查两项任务。

（2）引用类型

因为不存在所谓空引用，所以引用类型的dynamic_cast转换与指针类型不同，在引用转换失败时，会抛出std::bad_cast异常，该异常定义在头文件typeinfo中。

```c++
void f(const Base &b){ try{   const Derived &d = dynamic_cast<const Base &>(b);     //使用b引用的Derived对象 } catch(std::bad_cast){   //处理类型转换失败的情况 }}
```

## 转换注意事项

尽量少使用转型操作，尤其是dynamic_cast，耗时较高，会导致性能的下降，尽量使用其他方法替代。

# override

父类中的函数为虚函数,子类加上Overrie以避免忘记实现的错误.



# pthread

## join

## create





## boost::intrusive_ptr<CephContext>

