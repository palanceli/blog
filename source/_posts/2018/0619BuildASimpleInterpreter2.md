---
layout: post
title: 编写编译器和解释器二
date: 2018-06-19 14:00:00 +0800
categories: 编译器
tags: 随笔
toc: true
comments: true
---

<!-- more -->
# 将语法解析和解释执行分离
在Part7之前，语法解析和解释执行一直是合在一起的。这种解释其被称为**语法导向解释器**，这种解释器对源码进行一次遍历，适用于比较基本的语言处理程序。Part7开始讲两部分分离开，构建出源码的**中间表示形式Intermediate representation (IR)**，以应对更复杂的b编程语言。语法解析器负责构建IR，解释器则负责执行IR。

通过IR对源代码构建起的数据结构称为**抽象语法树abstract-syntax tree(AST)**，AST的每个非叶子节点代表一个运算符，叶子节点代表一个操作数。优先级越高的运算，放在AST中越靠近叶子的层级。下图是一个AST的示例：
![](0619BuildASimpleInterpreter2/img01.png)

和Part6相比，主要变化为：  
① 将Interpreter拆分为语法解析器Parser和解释器Interpreter
② 在Parser中`Parser::expr()`保持原先的逻辑框架，只是将原先的计算操作改为创建AST节点
③ 在Parser中按照语法解析每个非终结符时，原先的计算都改为创建一个AST节点
④ 在Interpreter中，它的主逻辑是`Interpreter::interprepret()`，负责后序遍历AST，计算结果

``` python
class AST(object):
    pass

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Parser(object):
    def __init__(self, lexer):
        ...

    def eat(self, token_type):
        ...

    def factor(self):
        ...

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        node = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)
            # ③ 将原先计算改为创建一个AST节点
            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)
            # ③ 将原先计算改为创建一个AST节点
            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        node = self.expr()
        ...

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    ...

class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser

    def visit_BinOp(self, node): # ④ 后序遍历AST
        if node.op.type == PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == DIV:
            return self.visit(node.left) / self.visit(node.right)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)
```