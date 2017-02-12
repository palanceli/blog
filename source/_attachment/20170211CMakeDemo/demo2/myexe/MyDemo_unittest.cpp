#include <gtest/gtest.h>
#include "MyDemo.h"
#include <stdio.h>


class MyDemoUnitTest : public testing::Test{
protected:
  static void SetUpTestCase(){}

  static void TearDownTestCase(){}
  MyDemoUnitTest();

};

MyDemoUnitTest::MyDemoUnitTest()
{
}

TEST_F(MyDemoUnitTest, Test1)
{
  MyDemo mydemo;
  mydemo.Fun1(100);
}
