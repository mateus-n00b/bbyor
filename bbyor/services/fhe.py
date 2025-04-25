from openfhe import *
from ..config.settings import settings
# 1. Inicializar o contexto
params = CCParamsBFVRNS()
params.SetPlaintextModulus(65537)
params.SetMultiplicativeDepth(2)
cc = GenCryptoContext(params)

cc.Enable(PKESchemeFeature.PKE)
cc.Enable(PKESchemeFeature.KEYSWITCH)
cc.Enable(PKESchemeFeature.LEVELEDSHE)
cc.Enable(PKESchemeFeature.ADVANCEDSHE)

# # 2. Gerar as chaves
# keys = cc.KeyGen()
# cc.EvalMultKeyGen(keys.secretKey)
# cc.EvalSumKeyGen(keys.secretKey)

# # 3. Criar plaintexts e cifrar
# a = 25
# b = 17

# pt_a = cc.MakePackedPlaintext([a])
# pt_b = cc.MakePackedPlaintext([b])

# ct_a = cc.Encrypt(keys.publicKey, pt_a)
# ct_b = cc.Encrypt(keys.publicKey, pt_b)

# # 4. Subtração homomórfica: a - b = c
# ct_result = cc.EvalSub(ct_a, ct_b)

# # 5. Decifrar o resultado
# pt_result = cc.Decrypt(keys.secretKey, ct_result)
# pt_result.SetLength(1)

# 6. Mostrar o resultado
# print(f"Resultado de {a} - {b} = {pt_result.GetPackedValue()[0]}")

def genKey() -> KeyPair:
    return cc.KeyGen()

def deserialize(a):
    return DeserializeCiphertextString(a, BINARY)

def serialize(a): 
    return Serialize(a, BINARY)
# Pk should be pk.bin
# Sk should be sk.bin
def serializeKeyToFile(dest: str, key) -> None:
    try: 
        SerializeToFile(dest, key, BINARY)
    except Exception as e:
        raise e

def loadPkFromFile(filename: str = settings.DEFAULT_DIR+"/pk.bin"):
    # DeserializePublicKeyString maybe
    return DeserializePublicKeyString(open(filename, 'rb').read(), BINARY)

def loadSkFromFile(filename: str = settings.DEFAULT_DIR+"/sk.bin"):
    return DeserializePrivateKeyString(open(filename, 'rb').read(), BINARY)

def makePackedList(value: str):
    return cc.MakePackedPlaintext([int(value)])

def evalSub(valueA: Ciphertext, valueB: int):
    _b = makePackedList(valueB)
    return cc.EvalSub(valueA, _b)

def evalAdd(valueA: Ciphertext, valueB: int):    
    _b = makePackedList(valueB)
    return cc.EvalAdd(valueA, _b)

def encrypt(value: int) -> Ciphertext:
    pk_a = makePackedList(value)    
    cc.EvalSumKeyGen(loadSkFromFile())
    a = cc.Encrypt(loadPkFromFile(), pk_a)
    
    return a