import copy
from collecitons import OrderedDict
from asdl.asdl import *
from asdl.asdl_ast import AbstractSyntaxTree
from alive.language import *
from alive.value import *
from alive.constants import *
from asdl.alive_form_helpers import *

## todo: get name for constants!
## todo make sure the way you're getting names is correct

def type_to_alive_form(ast_tree: AbstractSyntaxTree):
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
    else:
        print("constructor name was {}, didn't match with any instr constructors".format(constructor_name))
        raise ValueError
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
    else:
        print("constructor name was {}, didn't match with any instr constructors".format(constructor_name))
        raise ValueError
    # add new guy to idents
    idents.add(id)
    prog_idents[id] = outValue
    return out


def constant_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name == "ConstantVal":
        val = int(ast_tree["val"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        const = ConstantVal(val=val, type=t)
    elif constructor_name == "UndefVal":
        t = type_to_alive_form(ast_tree["t"].value)
        const = UndefVal(type=t)
    elif constructor_name == "CnstUnaryOp":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        v = ast_tree["val"].value
        const = CnstUnaryOp(op=op, v=v)
    elif constructor_name == "CnstBinaryOp":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        v1 = ast_tree["v1"].value
        v2 = ast_tree["v2"].value
        const = CnstBinaryOp(op=op, v1=v1, v2=v2)
    elif constructor_name == "CnstFunction":
        op = tree2cnstAliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        args = [value_to_alive_form(v) for v in ast_tree["args"].value]
        t = type_to_alive_form(ast_tree["t"].value)
        const = CnstFunction(op=op, args=args, type=t)
    else:
        print("constructor name was {}, didn't match with any instr constructors".format(constructor_name))
        raise ValueError
    # TODO: get the name of the constant!!
    idents.add(name)
    prog_idents[name] = const
    return const


def instrOperand_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    if constructor_name in assignInstrs:
        name, expr = instr_to_alive_form(ast_tree)
    elif constructor_name in const:
        expr = constant_to_alive_form(ast_tree)
    elif constructor_name in input:
        expr = value_to_alive_form(ast_tree)
    else:
        print("constructor name was {}, didn't match with any instr constructors".format(constructor_name))
        raise ValueError
    return expr


def instr_to_alive_form(ast_tree):
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
        v1 = instrOperand_to_alive_form(ast_tree["v1"].value)
        v2 = instrOperand_to_alive_form(ast_tree["v2"].value)
        # flag names are identical to strings used in the BinOp constructor
        flags = [v.production.constructor.name for v in ast_tree["flags"].value]
        expr = BinOp(op=op, type=t, v1=v1, v2=v2, flags=flags)
        stmt = (reg, expr)

    elif constructor_name == "ConversionOp":
        reg = ast_tree["reg"].value
        op = tree2AliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        st = type_to_alive_form(ast_tree["st"].value)
        v = instrOperand_to_alive_form(ast_tree["v"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        expr = ConversionOp(op=op, stype=st, v=v, type=t)
        stmt = (reg, expr)

    elif constructor_name == "Icmp":
        reg = ast_tree["reg"].value
        op = tree2AliveOp(asdl_name=ast_tree["op"].value, constructor_name=constructor_name)
        t = type_to_alive_form(ast_tree["t"].value)
        v1 = instrOperand_to_alive_form(ast_tree["v1"].value)
        v2 = instrOperand_to_alive_form(ast_tree["v2"].value)
        expr = Icmp(op=op, type=t, v1=v1, v2=v2)
        stmt = (reg, expr)

    elif constructor_name == "Select":
        reg = ast_tree["reg"].value
        t = type_to_alive_form(ast_tree["t"].value)
        # will be be icmp
        c = instr_to_alive_form(ast_tree["c"].value)
        v1 = instrOperand_to_alive_form(ast_tree["v1"].value)
        v2 = instrOperand_to_alive_form(ast_tree["v2"].value)
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
        v = instr_to_alive_form(ast_tree["v"].value)
        align = int(ast_tree["align"].value)
        expr = Load(stype=st, v=v, align=align)
        stmt = (reg, expr)

    # todo: you could make align optional and parse differently to make this easier
    elif constructor_name == "Store":
        id = "Store" + str(len(idents) + 1)
        st = type_to_alive_form(ast_tree["st"].value)
        src = instr_to_alive_form(ast_tree["src"].value)
        t = type_to_alive_form(ast_tree["t"].value)
        dst = instr_to_alive_form(ast_tree["dst"].value)
        align =int(ast_tree["align"].value)
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

    else:
        print("constructor name was {}, didn't match with any instr constructors".format(constructor_name))
        raise ValueError

    # add to the global prog dict
    # sometimes we may recursively call on instr and we'd like to add it first
    prog[id] = expr
    `prog_idents[id]` = expr
    # add the id to idents
    idents.add(id)

    return stmt

def prog_to_alive_form(ast_tree):
    constructor_name = ast_tree.production.constructor.name
    assert constructor_name == "Prog"
    global prog
    global prog_idents
    global idents
    prog = OrderedDict()
    prog_idents = OrderedDict()
    idents = set()
    for instr in ast_tree["instructions"].value:
        instr_to_alive_form(instr)
    return prog

def opt_to_alive_form(ast_tree):
    pre = ast_tree["precondition"].value if "precondition" in ast_tree.keys() else None
    src, src_idents = prog_to_alive_form(ast_tree["src"].value)
    tgt, tgt_idents = prog_to_alive_form(ast_tree["src"].value)
    return pre, src, src_idents, tgt, tgt_idents
