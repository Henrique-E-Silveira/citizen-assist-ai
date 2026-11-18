"""Classe Orientacao: uma informação da base de conhecimento (um registro do JSON)."""

CAMPOS_OBRIGATORIOS = ("id", "categoria", "titulo", "palavras_chave", "resposta",
                       "documentos", "onde", "fonte", "verificado_em")

AVISO = "este assistente NÃO é um canal oficial."


class Orientacao:
    """Guarda os dados de uma orientação e sabe se mostrar na tela."""

    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em

    @classmethod
    def de_dicionario(cls, dados):
        """Cria uma Orientacao a partir de um dicionário lido do JSON.

        Levanta ValueError se faltar algum campo ou se o tipo estiver errado.
        """
        if not isinstance(dados, dict):
            raise ValueError("registro não é um dicionário")
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
        if faltando:
            raise ValueError("campos faltando: " + ", ".join(faltando))
        if not isinstance(dados["palavras_chave"], list) or not isinstance(dados["documentos"], list):
            raise ValueError("palavras_chave e documentos devem ser listas")
        return cls(**{campo: dados[campo] for campo in CAMPOS_OBRIGATORIOS})

    def exibir(self):
        """Mostra a orientação completa, com fonte, data e aviso."""
        print()
        print(f">> {self.titulo}  [{self.categoria}]")
        print(self.resposta)
        print("Documentos necessários:")
        for documento in self.documentos:
            print(f"  - {documento}")
        print(f"Onde: {self.onde}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(f"Aviso: {AVISO}")
        print()
