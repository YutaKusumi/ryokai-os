"""
近似トークナイザ（Qwen2 語彙・GGUF から再構成）。
検証: BP の四文で 68 / 18 / 23 / 28、合計 137 を再現（2026-09-02）。
正式実測は Qwen3 の公式トークナイザで行うこと。
依存: pip install gguf tokenizers
語彙: https://raw.githubusercontent.com/ggml-org/llama.cpp/master/models/ggml-vocab-qwen2.gguf
"""
import sys
from gguf import GGUFReader
from tokenizers import Tokenizer, models, pre_tokenizers, decoders, Regex

def build(gguf_path):
    r = GGUFReader(gguf_path)
    def strs(f): return [bytes(f.parts[i]).decode('utf-8') for i in f.data]
    tokens = strs(r.fields['tokenizer.ggml.tokens'])
    merges = strs(r.fields['tokenizer.ggml.merges'])
    tok = Tokenizer(models.BPE(vocab={t:i for i,t in enumerate(tokens)},
                               merges=[tuple(m.split(' ')) for m in merges], byte_fallback=False))
    pat = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
    tok.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Split(Regex(pat), behavior='isolated'),
        pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)])
    tok.decoder = decoders.ByteLevel()
    return tok

if __name__ == '__main__':
    tok = build(sys.argv[1] if len(sys.argv) > 1 else 'ggml-vocab-qwen2.gguf')
    for line in sys.stdin:
        line = line.rstrip('\n')
        if line: print(len(tok.encode(line).ids), line)
