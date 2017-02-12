#include <stdio.h>
#include "MyDemo.h"
#include "MyLib.h"

int main(int argc, char* argv[])
{
  MyDemo mydemo;
  mydemo.Fun1(100);
  MyLibFun1(200);
  printf("hello world!\n");
}
