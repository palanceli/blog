#include <gtest/gtest.h>
#include "MyLib.h"
#include <stdio.h>


class MyLibUnitTest : public testing::Test{
protected:
  static void SetUpTestCase(){}

  static void TearDownTestCase(){}
  MyLibUnitTest();

};

MyLibUnitTest::MyLibUnitTest()
{
}

TEST_F(MyLibUnitTest, Test1)
{
  MyLibFun1(100);
}
