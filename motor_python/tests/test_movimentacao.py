import os
import sqlite3
import tempfile
from datetime import datetime

import pytest
import xxhash

# Importamos o worker a ser testado
# Obs: O import pode falhar se a classe ainda nao existir no momento do setup inicial,
# mas ela sera criada logo a seguir.
from movement_worker import MovementWorker


@pytest.fixture
def temp_env():
    """Cria uma estrutura de pastas temporarias para testes de movimentacao."""
    with tempfile.TemporaryDirectory() as base_dir:
        origem = os.path.join(base_dir, "origem")
        destino = os.path.join(base_dir, "destino")
        os.makedirs(origem, exist_ok=True)
        os.makedirs(destino, exist_ok=True)

        db_path = os.path.join(base_dir, "teste.sqlite")

        yield {
            "base_dir": base_dir,
            "origem": origem,
            "destino": destino,
            "db_path": db_path
        }

def setup_db(db_path):
    """Inicializa as tabelas necessarias no banco de dados de teste."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_processamento (
            uuid TEXT PRIMARY KEY,
            dispositivo_id INTEGER,
            caminho_origem TEXT UNIQUE,
            nome_original TEXT,
            tamanho_bytes INTEGER,
            hash_xxhash TEXT,
            status TEXT DEFAULT 'pendente_extracao',
            caminho_proposto TEXT,
            caminho_aprovado TEXT,
            categoria_proposta TEXT,
            justificativa_classificacao TEXT,
            eh_duplicado INTEGER DEFAULT 0,
            motivo_falha TEXT,
            mensagem_erro TEXT,
            data_criacao_sistema INTEGER,
            data_modificacao_sistema INTEGER,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_processamento TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            texto_extraido TEXT
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS categorias_destino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_macro TEXT NOT NULL,
            categoria_micro TEXT NOT NULL UNIQUE,
            caminho_relativo_pasta TEXT NOT NULL,
            descricao_busca TEXT NOT NULL,
            vetor_embedding BLOB,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_processamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_uuid TEXT,
            componente TEXT NOT NULL,
            nivel TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            data_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (arquivo_uuid) REFERENCES arquivos_processamento(uuid) ON DELETE SET NULL
        );
        """)

        # Insere algumas categorias para teste
        conn.execute("""
        INSERT INTO categorias_destino (categoria_macro, categoria_micro, caminho_relativo_pasta, descricao_busca)
        VALUES
        ('Resources', 'r_manuais', 'Resources/Manuais', 'Manuais de instrucao e manuais de software'),
        ('Archives', 'v_outros', 'Archives/Outros', 'Backups antigos e outros arquivos expirados');
        """)

        conn.commit()
    finally:
        conn.close()

def test_movimentacao_sucesso(temp_env):
    """Verifica se um arquivo aprovado e movido corretamente, validado por hash e com timestamps preservados."""
    setup_db(temp_env["db_path"])

    # Criamos um arquivo na origem
    caminho_origem = os.path.join(temp_env["origem"], "manual_impressora.pdf")
    conteudo = b"Conteudo do manual de instrucao da impressora."
    with open(caminho_origem, "wb") as f:
        f.write(conteudo)

    # Capturamos timestamps originais
    stat_origem = os.stat(caminho_origem)
    data_criacao = int(stat_origem.st_ctime)
    data_modificacao = int(stat_origem.st_mtime)

    h_original = xxhash.xxh64(conteudo).hexdigest()

    # Cadastramos no banco
    conn = sqlite3.connect(temp_env["db_path"])
    try:
        conn.execute("""
        INSERT INTO arquivos_processamento
        (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema, caminho_aprovado, categoria_proposta)
        VALUES
        ('uuid-pdf', ?, 'manual_impressora.pdf', ?, ?, 'aprovado_para_movimentacao', ?, ?, ?, 'r_manuais')
        """, (caminho_origem, len(conteudo), h_original, data_criacao, data_modificacao, temp_env["destino"]))
        conn.commit()
    finally:
        conn.close()

    worker = MovementWorker(temp_env["db_path"], temp_env["destino"])
    processados = worker.execute()

    assert processados == 1

    # O arquivo original de origem deve ter sido apagado
    assert not os.path.exists(caminho_origem)

    # O arquivo deve estar no destino correto (Resources/Manuais/YYYYMMDD_manual_impressora.pdf)
    caminho_destino_esperado = os.path.normpath(os.path.join(
        temp_env["destino"],
        "Resources",
        "Manuais",
        f"{datetime.fromtimestamp(data_criacao).strftime('%Y%m%d')}_manual_impressora.pdf"
    ))

    assert os.path.exists(caminho_destino_esperado)

    # Validamos integridade física (hash)
    with open(caminho_destino_esperado, "rb") as f:
        h_destino = xxhash.xxh64(f.read()).hexdigest()
    assert h_destino == h_original

    # Validamos os timestamps de destino
    stat_destino = os.stat(caminho_destino_esperado)

    # Em sistemas Windows, ctypes define a data de criacao com precisao
    # st_ctime no Windows representa a data de criacao
    assert int(stat_destino.st_ctime) == data_criacao
    assert int(stat_destino.st_mtime) == data_modificacao

    # Verificamos no banco se o status passou para 'concluido'
    conn = sqlite3.connect(temp_env["db_path"])
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, caminho_aprovado FROM arquivos_processamento WHERE uuid='uuid-pdf'")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 'concluido'
        assert row[1] == caminho_destino_esperado
    finally:
        conn.close()

def test_descarte_pendente(temp_env):
    """Garante que arquivos com descarte_pendente sejam movidos para a pasta local _TRASH_."""
    setup_db(temp_env["db_path"])

    # Criamos um arquivo na origem a ser descartado
    caminho_origem = os.path.join(temp_env["origem"], "documento_duplicado.docx")
    conteudo = b"Conteudo duplicado ou lixo."
    with open(caminho_origem, "wb") as f:
        f.write(conteudo)

    h_original = xxhash.xxh64(conteudo).hexdigest()

    conn = sqlite3.connect(temp_env["db_path"])
    try:
        conn.execute("""
        INSERT INTO arquivos_processamento
        (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema)
        VALUES
        ('uuid-trash', ?, 'documento_duplicado.docx', ?, ?, 'descarte_pendente', 1234567, 1234567)
        """, (caminho_origem, len(conteudo), h_original))
        conn.commit()
    finally:
        conn.close()

    worker = MovementWorker(temp_env["db_path"], temp_env["destino"])
    processados = worker.execute()

    assert processados == 1
    assert not os.path.exists(caminho_origem)

    # O arquivo deve estar no destino local de _TRASH_
    caminho_lixeira_esperado = os.path.join(temp_env["destino"], "_TRASH_", "documento_duplicado.docx")
    assert os.path.exists(caminho_lixeira_esperado)

    # O status do banco deve passar para 'descartado'
    conn = sqlite3.connect(temp_env["db_path"])
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, caminho_aprovado FROM arquivos_processamento WHERE uuid='uuid-trash'")
        row = cursor.fetchone()
        assert row[0] == 'descartado'
        assert row[1] == caminho_lixeira_esperado
    finally:
        conn.close()

def test_tratamento_homonimos_diferentes(temp_env):
    """Verifica que se um arquivo com mesmo nome mas conteudo diferente existir no destino, aplica sufixo _vXX."""
    setup_db(temp_env["db_path"])

    # 1. Copiamos o primeiro arquivo manual.pdf para o destino manualmente para simular colisao
    pasta_destino_pdf = os.path.join(temp_env["destino"], "Resources", "Manuais")
    os.makedirs(pasta_destino_pdf, exist_ok=True)

    data_criacao = 10000000
    prefixo_data = datetime.fromtimestamp(data_criacao).strftime('%Y%m%d')
    nome_final_esperado = f"{prefixo_data}_manual.pdf"

    caminho_colisao = os.path.join(pasta_destino_pdf, nome_final_esperado)
    with open(caminho_colisao, "wb") as f:
        f.write(b"Conteudo do manual antigo.")

    # 2. Criamos o segundo arquivo manual.pdf na origem (conteudo diferente)
    caminho_origem = os.path.join(temp_env["origem"], "manual.pdf")
    conteudo_novo = b"Conteudo do novo manual de instrucoes."
    with open(caminho_origem, "wb") as f:
        f.write(conteudo_novo)

    h_original = xxhash.xxh64(conteudo_novo).hexdigest()

    conn = sqlite3.connect(temp_env["db_path"])
    try:
        conn.execute("""
        INSERT INTO arquivos_processamento
        (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema, caminho_aprovado, categoria_proposta)
        VALUES
        ('uuid-colisao', ?, 'manual.pdf', ?, ?, 'aprovado_para_movimentacao', ?, ?, ?, 'r_manuais')
        """, (caminho_origem, len(conteudo_novo), h_original, data_criacao, data_criacao, temp_env["destino"]))
        conn.commit()
    finally:
        conn.close()

    worker = MovementWorker(temp_env["db_path"], temp_env["destino"])
    processados = worker.execute()

    assert processados == 1
    assert not os.path.exists(caminho_origem)

    # O arquivo com colisao deve estar nomeado com _v01
    nome_sufixo_esperado = f"{prefixo_data}_manual_v01.pdf"
    caminho_novo_destino = os.path.join(pasta_destino_pdf, nome_sufixo_esperado)

    assert os.path.exists(caminho_novo_destino)
    assert os.path.exists(caminho_colisao) # O antigo continua la intacto

    # Verifica hash do novo
    with open(caminho_novo_destino, "rb") as f:
        assert xxhash.xxh64(f.read()).hexdigest() == h_original

def test_falha_validacao_hash(temp_env):
    """Garante que se a gravacao falhar ou o hash nao bater, o arquivo de origem nao e apagado e o status muda para erro."""
    setup_db(temp_env["db_path"])

    caminho_origem = os.path.join(temp_env["origem"], "manual_corrompido.pdf")
    conteudo = b"Conteudo que vai falhar na validacao."
    with open(caminho_origem, "wb") as f:
        f.write(conteudo)

    # Colocamos um hash incorreto no banco de dados para forcar a falha na validacao
    h_incorreto = "hash-totalmente-errado-123"

    conn = sqlite3.connect(temp_env["db_path"])
    try:
        conn.execute("""
        INSERT INTO arquivos_processamento
        (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema, caminho_aprovado, categoria_proposta)
        VALUES
        ('uuid-falha', ?, 'manual_corrompido.pdf', ?, ?, 'aprovado_para_movimentacao', 1000, 1000, ?, 'r_manuais')
        """, (caminho_origem, len(conteudo), h_incorreto, temp_env["destino"]))
        conn.commit()
    finally:
        conn.close()

    worker = MovementWorker(temp_env["db_path"], temp_env["destino"])
    processados = worker.execute()

    # Processado com falha interna, nao deve contar como sucesso/concluido
    assert processados == 1 # O loop executou para o arquivo

    # O arquivo original de origem deve continuar existindo!
    assert os.path.exists(caminho_origem)

    # O status deve ser 'erro' no banco de dados
    conn = sqlite3.connect(temp_env["db_path"])
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, mensagem_erro FROM arquivos_processamento WHERE uuid='uuid-falha'")
        row = cursor.fetchone()
        assert row[0] == 'erro'
        assert "Falha na integridade" in row[1]
    finally:
        conn.close()

def test_teardown_pastas_vazias(temp_env):
    """Verifica se pastas que ficaram vazias na origem sao devidamente removidas, preservando a pasta de origem raiz."""
    setup_db(temp_env["db_path"])

    # Criamos uma estrutura de pastas na origem:
    # origem/sub1/sub2/arquivo.pdf
    sub1 = os.path.join(temp_env["origem"], "sub1")
    sub2 = os.path.join(sub1, "sub2")
    os.makedirs(sub2, exist_ok=True)

    caminho_origem = os.path.join(sub2, "manual.pdf")
    conteudo = b"Conteudo do manual"
    with open(caminho_origem, "wb") as f:
        f.write(conteudo)

    h_original = xxhash.xxh64(conteudo).hexdigest()

    conn = sqlite3.connect(temp_env["db_path"])
    try:
        conn.execute("""
        INSERT INTO arquivos_processamento
        (uuid, caminho_origem, nome_original, tamanho_bytes, hash_xxhash, status, data_criacao_sistema, data_modificacao_sistema, caminho_aprovado, categoria_proposta)
        VALUES
        ('uuid-teardown', ?, 'manual.pdf', ?, ?, 'aprovado_para_movimentacao', 1000, 1000, ?, 'r_manuais')
        """, (caminho_origem, len(conteudo), h_original, temp_env["destino"]))
        conn.commit()
    finally:
        conn.close()

    worker = MovementWorker(temp_env["db_path"], temp_env["destino"])
    # Passamos o diretorio de origem monitorado para que ele faca o teardown dele de forma segura
    worker.origem_monitorada = temp_env["origem"]

    processados = worker.execute()

    assert processados == 1
    assert not os.path.exists(caminho_origem)

    # A estrutura sub1 e sub2 deve ter sido removida, pois ficaram vazias
    assert not os.path.exists(sub2)
    assert not os.path.exists(sub1)

    # Mas a raiz da origem monitorada continua existindo!
    assert os.path.exists(temp_env["origem"])
