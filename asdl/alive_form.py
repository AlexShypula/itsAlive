# todo see parseInstr for handling of ids in assignInstructions

import copy
from asdl.asdl import *
from asdl.asdl_ast import AbstractSyntaxTree
from alive.language import *
from alive.value import *
from alive.constants import *
from asdl.alive_form_helpers import *


global idents = set()


def type_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name == "UnknownType":
        depth = ast_tree["depth"].value if "depth" in ast_tree.keys() else 0
        t = UnknownType(d=depth)
    elif constructor_name == "NamedType":
        name = ast_tree["name"].value
        t = NamedType(name=name)
    elif constructor_name == "IntType":
        size = ast_tree["size"].value if "size" in ast_tree.keys() else None
        t = UnknownType(d=size)
    elif constructor_name == "PtrType":
        underlyingType = type_to_alive_form(ast_tree["t"].value) if "t" in ast_tree.keys() else None
        depth = ast_tree["depth"].value if "depth" in ast_tree.keys() else 0
        t = PtrType(type=underlyingType, depth=depth)
    elif constructor_name == "Array":
        ### if elems not none, then it is turned into TypeFixedValue
        ### TypeFixedValue receives v, which must be a value with .type IntType and is a subclass of Value
        elems = value_to_alive_form(ast_tree["elems"].value) if "t" in ast_tree.keys() else None
        underlyingType = type_to_alive_form(ast_tree["t"].value) if "t" in ast_tree.keys() else None
        depth = ast_tree["depth"].value if "depth" in ast_tree.keys() else 0
        t = ArrayType(elems=elems, type=underlyingType, depth=depth)
    return t


def value_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name == "TypeFixedValue":
        id = ast_tree["name"].value
        v = value_to_alive_form(ast_tree["v"].value)
        min = int(ast_tree["min"].value)
        max = int(ast_tree["max"].value)
        outValue = TypeFixedValue(v=v, min=min, max=max)
        out = (id, outValue)
    elif constructor_name == "Input":
        id = ast_tree["name"].value
        t = type_to_alive_form(ast_tree["t"].value)
        outValue = Input(name=id, type=t)
        out = (id, outValue)
    idents.add(id)
    return out


def constant_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name == "ConstantVal":
        val = int(ast_tree["val"].value) # todo, can we go beyond int
        t = type_to_alive_form(ast_tree["t"].value)
        const = ConstantVal(val=val, type=t)
    elif constructor_name == "UndefVal":
        t = type_to_alive_form(ast_tree["t"].value)
        const = UndefVal(type=t)
    elif constructor_name == "CnstUnaryOp":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_na,e):
        v = ast_tree["val"].value
        const = CnstUnaryOp(op=op, v=v)
    elif constructor_name == "CnstBinaryOp":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        v1 = ast_tree["v1"].value
        v2 = ast_tree["v2"].value
        const = CnstBinaryOp(op=op, v1=v1, v2=v2)
    elif constructor_name == "CnstFunction":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        # todo !! how to parse something with multiple fields??!!!
        args = [value_to_alive_form(v) for v in ast_tree["args"].value]
        t = type_to_alive_form(ast_tree["t"].value)
        const = CnstFunction(op=op, args=args, type=t)
    return const

def stmt_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name == "CopyOperand":
        reg = ast_tree["reg"].value
        v = value_to_alive_form(ast_tree["v"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        expr = CopyOperand(v=v, type=t)
        stmt = (reg, expr)

    elif constructor_name == "BinOp":
        reg = ast_tree["reg"].value
        op = tree2AliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        t = type_to_alive_form(ast_tree["t"].value)
        v1 = value_to_alive_form(ast_tree["v1"].value)
        v2 = value_to_alive_form(ast_tree["v2"].value)
        # todo how do I parse out lists
        flags = [v.production.constructor.name for v in ast_tree["flags"].value]
        expr = BinOp(op=op, type=t, v1=v1, v2=v2, flags=flags)
        stmt = (reg, expr)

    elif constructor_name == "ConversionOp":
        reg = ast_tree["reg"].value
        op = tree2AliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        st = type_to_alive_form(ast_tree["st"].value)
        v = value_to_alive_form(ast_tree["v"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        expr = ConversionOp(op=op, stype=st, v=v, type=t)
        stmt = (reg, expr)

    elif constructor_name == "Icmp":
        reg = ast_tree["reg"].value
        op = tree2AliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        t = type_to_alive_form(ast_tree["t"].value)
        v1 = value_to_alive_form(ast_tree["v1"].value)
        v2 = value_to_alive_form(ast_tree["v2"].value)
        expr = Icmp(op=op, type=t, v1=v1, v2=v2)
        stmt = (reg, expr)

    elif constructor_name == "Select":
        reg = ast_tree["reg"].value
        t = type_to_alive_form(ast_tree["t"].value)
        c = ast_tree["c"].value # todo: parse conditional
        v1 = value_to_alive_form(ast_tree["v1"].value)
        v2 = value_to_alive_form(ast_tree["v2"].value)
        expr = Select(type=t, c=c, v1=v1, v2=v2)
        stmt = (reg, expr)

    # todo: you could make align optional and parse differently to make this easier
    elif constructor_name == "Alloca":
        reg = ast_tree["reg"].value
        t = type_to_alive_form(ast_tree["t"].value)
        elemsType = type_to_alive_form(ast_tree["elemnsType"].value)
        # num elems is passed onto TypeFixedValue inside Alloca, so it must be of type Value
        numElems = value_to_alive_form(ast_tree["numElems"].value)
        align = int(ast_tree["align"].value)
        expr = Alloca(type=t, elemsType=elemsType, numElems=numElems, align=align)
        stmt = (reg, expr)

    # todo
    elif constructor_name == "GEP":
        # t = ast_tree["t"].value
        # pte = ast_tree["prt"].value
        raise NotImplementedError

    # todo: you could make align optional and parse differently to make this easier
    elif constructor_name == "Load":
        reg = ast_tree["reg"].value
        st = type_to_alive_form(ast_tree["st"].value)
        v = value_to_alive_form(ast_tree["v"].value)
        align = int(ast_tree["align"].value)
        expr = Load(stype=st, v=v, align=align)
        stmt = (reg, expr)

    # todo: you could make align optional and parse differently to make this easier
    elif constructor_name == "Store":
        id = "Store" + str(len(idents) + 1)
        st = type_to_alive_form(ast_tree["st"].value)
        src = value_to_alive_form(ast_tree["src"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        dst = value_to_alive_form(ast_tree["dst"].value)
        align =int(ast_tree["align"].value))
        expr = Store(stype=st, src=src, type=t, dst=dst, align=align)
        stmt = (id, expr)

    # todo bb label
    elif constructor_name == "Br":
        raise NotImplementedError
        # id = "Br" + str(len(idents) + 1)
        # bb_label = ast_tree["bb_label"].value
        # cond = ast_tree["cond"].value
        # true = ast_tree["true"].value
        # false = ast_tree["false"].value
        # expr = Br(bb_label=bb_label, cond=cond, true=true, false=false)
        # stmt = (id, expr)

    elif constructor_name == "Ret":
        raise NotImplementedError
        # id = "Ret" + str(len(idents) + 1)
        # bb_label = ast_tree["bb_label"].value
        # t = ast_tree["t"].value
        # val = ast_tree["val"].value
        # expr = Ret(bb_label=bb_label, type=t, val=val)
        # stmt = (id, expr)

    elif constructor_name == "Skip":
        id = "Skip" + str(len(idents) + 1)
        expr = Skip()
        stmt = (id, expr)

    elif constructor_name == "Unreachable":
        id = "Unreachable" + str(len(idents) + 1)
        expr = Unreachable
        stmt = (id, expr)

    # add the id to idents
    idents.add(id)
    # todo setattr to main / globals with the ID

    return stmt

from collecitons import OrderedDict

def prog_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    assert constructor_name == "Prog"
    prog = OrderedDict()
    for instr in ast_tree["instructions"].value:
        id, expr = stmt_to_alive_form(instr)
        prog[id] = expr
    return prog




#
# def ast_to_logical_form(ast_tree):
#     constructor_name = ast_tree.production.constructor.name
#     if constructor_name == 'Lambda':
#         var_node = Node(ast_tree['variable'].value)
#         type_node = Node(ast_tree['type'].value)
#         body_node = ast_to_logical_form(ast_tree['body'].value)
#
#         node = Node('lambda', [var_node, type_node, body_node])
#     elif constructor_name in ['Argmax', 'Argmin', 'Sum']:
#         var_node = Node(ast_tree['variable'].value)
#         domain_node = ast_to_logical_form(ast_tree['domain'].value)
#         body_node = ast_to_logical_form(ast_tree['body'].value)
#
#         node = Node(constructor_name.lower(), [var_node, domain_node, body_node])
#     elif constructor_name == 'Apply':
#         predicate = ast_tree['predicate'].value
#         arg_nodes = [ast_to_logical_form(tree) for tree in ast_tree['arguments'].value]
#
#         node = Node(predicate, arg_nodes)
#     elif constructor_name in ['Count', 'Exists', 'Max', 'Min', 'The']:
#         var_node = Node(ast_tree['variable'].value)
#         body_node = ast_to_logical_form(ast_tree['body'].value)
#
#         node = Node(constructor_name.lower(), [var_node, body_node])
#     elif constructor_name in ['And', 'Or']:
#         arg_nodes = [ast_to_logical_form(tree) for tree in ast_tree['arguments'].value]
#
#         node = Node(constructor_name.lower(), arg_nodes)
#     elif constructor_name == 'Not':
#         arg_node = ast_to_logical_form(ast_tree['argument'].value)
#
#         node = Node('not', arg_node)
#     elif constructor_name == 'Compare':
#         op = {'GreaterThan': '>', 'Equal': '=', 'LessThan': '<'}[ast_tree['op'].value.production.constructor.name]
#         left_node = ast_to_logical_form(ast_tree['left'].value)
#         right_node = ast_to_logical_form(ast_tree['right'].value)
#
#         node = Node(op, [left_node, right_node])
#     elif constructor_name in ['Variable', 'Entity', 'Number']:
#         node = Node(ast_tree.fields[0].value)
#     else:
#         raise ValueError('unknown AST node %s' % ast_tree)
#
#     return node