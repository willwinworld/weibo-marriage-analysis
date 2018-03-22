#! python3
# -*- coding: utf-8 -*-


# class Node:
#     def __init__(self, val):
#         self.left = None
#         self.right = None
#         self.val = val


class BinaryTree:
    """
    Problem Solving with Algorithms and Data Structures
    比较基本的实现方式，没有采用递归插入
    """
    def __init__(self, root):
        self.key = root
        self.left_child = None
        self.right_child = None

    def insert_left(self, new_node):
        if self.left_child is None:
            self.left_child = BinaryTree(new_node)
        else:
            t = BinaryTree(new_node)  # 要插入的结点
            t.left_child = self.left_child  # self.left_child为要插入的结点的左孩子，这时让新的节点的儿子左孩子赋给它，也就是往下降了一级
            self.left_child = t

    def insert_right(self, new_node):
        if self.right_child is None:
            self.right_child = BinaryTree(new_node)
        else:
            t = BinaryTree(new_node)
            t.right_child = self.right_child  #
            self.right_child = t

    def get_left_child(self):
        return self.left_child

    def get_right_child(self):
        return self.right_child

    def set_root_val(self, obj):
        self.key = obj  # stores the object in parameter val in the current node

    def get_root_val(self):
        return self.key  # returns the object stored in the current node.


def build_tree():
    root = BinaryTree('a')  # 设置根结点
    print(root.get_root_val())

    root.insert_left('b')  # 插入左孩子结点
    print(root.get_left_child())
    print(root.get_left_child().get_root_val())
    root.insert_right('c')  # 插入右孩子结点
    print(root.get_right_child())
    print(root.get_right_child().get_root_val())

    root.left_child.insert_right('d')
    print(root.left_child.get_right_child())
    print(root.left_child.get_right_child().get_root_val())
    root.right_child.insert_left('e')
    print(root.right_child.get_left_child())
    print(root.right_child.get_left_child().get_root_val())
    root.right_child.insert_right('f')
    print(root.right_child.get_right_child())
    print(root.right_child.get_right_child().get_root_val())


class Node:
    def __init__(self, data, left=None, right=None):
        self.left = left
        self.right = right
        self.data = data

    def insert(self, data):
        if self.data:
            if data < self.data:
                if self.left is None:
                    self.left = Node(data)
                else:
                    self.left.insert(data)  # 递归插入
            elif data > self.data:
                if self.right is None:
                    self.right = Node(data)  # 递归插入
                else:
                    self.right.insert(data)
        else:
            self.data = data

    def lookup(self, data, parent=None):
        if data < self.data:
            if self.left is None:
                return None, None
            return self.left.lookup(data, self)
        elif data > self.data:
            if self.right is None:
                return None, None
            return self.right.lookup(data, self)
        else:
            return self, parent

    def children_count(self):
        cnt = 0
        if self.left:
            cnt += 1
        if self.right:
            cnt += 1
        return cnt

    def delete(self, data):
        node, parent = self.lookup(data)
        if node is not None:
            children_count = node.children_count()
            if children_count == 0:
                if parent:
                    if parent.left is node:
                        parent.left = None
                    else:
                        parent.right = None
                    del node
                else:
                    self.data = None


# class TransmitTree(object):
#     def __init__(self):



if __name__ == '__main__':
    # r = BinaryTree('a')
    # print('--------------------')
    # print(r.get_root_val())  # 获取根结点
    # print(r.get_left_child())  # 获取左孩子
    # print('--------------------')
    #
    # r.insert_left('b')
    # print('********************')
    # print(r.get_left_child())  # 获取左孩子的内存地址
    # print(r.get_left_child().get_root_val())  # 获取左孩子的内存地址的值
    # print('********************')
    #
    # r.insert_right('c')
    # print('$$$$$$$$$$$$$$$$$$$$')
    # print(r.get_right_child())  # 获取右孩子的内存地址
    # print(r.get_right_child().get_root_val())  # 获取右孩子的内存地址的值
    # print('$$$$$$$$$$$$$$$$$$$$')
    #
    # r.get_right_child().set_root_val('hello')  # 将右结点的值设置为hello
    # print('%%%%%%%%%%%%%%%%%%%%')
    # print(r.get_right_child().get_root_val())  # 获得右结点的值
    # print('%%%%%%%%%%%%%%%%%%%%')

    build_tree()
