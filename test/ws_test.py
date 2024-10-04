import binascii
#
hex_data = ''
# unhexlify 返回由十六进制字符串 hexstr 表示的二进制数据
data = binascii.unhexlify(hex_data)
# 然后把它用二进制的形式写入文件，记住，不能直接复制到文件中
with open('my-protobuf', 'wb') as w:
    w.write(data)


# data = '3a02 6862'.replace(' ', '')
# print(binascii.unhexlify(data).decode())
