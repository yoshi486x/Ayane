import codecs


class Reader:
    @staticmethod
    def read_str(path):
        for enc in ['cp932', 'utf-8-sig']:
            try:
                with codecs.open(path, 'r', enc) as f:
                    return f.read()
            except:
                pass
        return None
    
