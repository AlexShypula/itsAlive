from alive.language import Icmp, BinOp, ConversionOp

icmpTree2OpName = {
    'EQ': 'eq',
    'NE': 'ne',
    'UGT': 'ugt',
    'UGE': 'uge',
    'ULT': 'ult',
    'ULE': 'ule',
    'SGT': 'sgt',
    'SGE': 'sge',
    'SLT': 'slt',
    'SLE': 'sle',
}


conversionOpTree2OpName = {
    'Trunc': 'trunc',
    'ZExt': 'zext',
    'SExt': 'sext',
    'ZExtOrTrunc': 'ZExtOrTrunc',
    'Ptr2Int': 'ptrtoint',
    'Int2Ptr': 'inttoptr',
    'Bitcast': 'bitcast',
  }


binOpTree2OpName = {
    'Add':  'add',
    'Sub':  'sub',
    'Mul':  'mul',
    'UDiv': 'udiv',
    'SDiv': 'sdiv',
    'URem': 'urem',
    'SRem': 'srem',
    'Shl':  'shl',
    'AShr': 'ashr',
    'LShr': 'lshr',
    'And':  'and',
    'Or':   'or',
    'Xor':  'xor',
  }

def tree2AliveOp(asdl_name: str, constructor_name: str):
    if constructor_name == "BinOp":
        opName = binOpTree2OpName[asdl_name]
        op = BinOp.getOpId(opName)
    elif constructor_name == "ConversionOp":
        opName = conversionOpTree2OpName[asdl_name]
        op = ConversionOp.getOpId(opName)
    elif constructor_name == "Icmp":
        ## Icmp is different where we pass in the opName !
        op = conversionOpTree2OpName[asdl_name]
    return op