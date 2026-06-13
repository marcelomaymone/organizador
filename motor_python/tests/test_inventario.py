import sqlite3

import pytest

from inventario import DatabaseRepository, Hasher, InventoryWorker, Scanner, SecurityError

# Usamos fixture do pytest para criar caminhos e ambientes isolados para os testes,
# garantindo que o estado do banco e dos arquivos nao vaze entre execucoes (SOLID - Principio de Responsabilidade Unica).

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture que cria um diretorio de origem temporario para testes de varredura."""
    d = tmp_path / "origem_teste"
    d.mkdir()
    return d

@pytest.fixture
def temp_db(tmp_path):
    """Fixture que cria um caminho temporario para o banco de dados SQLite de teste."""
    return str(tmp_path / "teste.sqlite")

def test_scanner_prohibited_paths():
    """Garante que o Scanner lanca SecurityError para caminhos criticos de sistema."""
    # Testamos a raiz C:\ que e proibida
    with pytest.raises(SecurityError):
        Scanner("C:\\")

    with pytest.raises(SecurityError):
        Scanner("C:")

    # Testamos pastas protegidas especificas
    for path in Scanner.PROHIBITED_PATHS:
        with pytest.raises(SecurityError):
            Scanner(path)

def test_scanner_scan_files(temp_dir):
    """Garante que o Scanner indexa corretamente os arquivos no diretorio permitido."""
    # Criamos alguns arquivos de teste dentro da pasta temporaria permitida
    file1 = temp_dir / "arquivo1.txt"
    file1.write_text("Conteudo do primeiro arquivo de teste.")

    file2 = temp_dir / "arquivo2.txt"
    file2.write_text("Outro conteudo.")

    # Criamos subdiretorios
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    file3 = subdir / "arquivo3.txt"
    file3.write_text("Conteudo do subdiretorio.")

    scanner = Scanner(str(temp_dir))
    files = list(scanner.scan_files())

    # Devem ser encontrados 3 arquivos
    assert len(files) == 3
    caminhos = [f['caminho'] for f in files]
    assert str(file1) in caminhos
    assert str(file2) in caminhos
    assert str(file3) in caminhos

def test_hasher_compute_xxhash(temp_dir):
    """Verifica se o Hasher computa o hash xxhash corretamente usando blocos de leitura."""
    test_file = temp_dir / "hash_test.dat"
    test_file.write_bytes(b"hello world")

    # O hash xxhash xxh64 esperado para 'hello world' e 45ab6734b21e6968
    expected_hash = "45ab6734b21e6968"
    actual_hash = Hasher.compute_xxhash(str(test_file))

    assert actual_hash == expected_hash

def test_database_repository_insert_and_conflict(temp_db):
    """Valida se o repositorio insere dados corretamente e gerencia conflitos (Upsert)."""
    # Precisamos criar as tabelas necessarias no banco de dados temporario de teste.
    # Como as tabelas ja sao criadas no banco oficial via migrations do Laravel,
    # aqui recriamos o schema basico apenas para fins de teste isolado do repositorio.
    conn = sqlite3.connect(temp_db)
    try:
        conn.execute("""
        CREATE TABLE arquivos_processamento (
            uuid TEXT PRIMARY KEY,
            caminho_origem TEXT UNIQUE,
            nome_original TEXT,
            tamanho_bytes INTEGER,
            hash_xxhash TEXT,
            status TEXT,
            data_criacao_sistema INTEGER,
            data_modificacao_sistema INTEGER,
            justificativa_classificacao TEXT,
            eh_duplicado INTEGER,
            motivo_falha TEXT,
            mensagem_erro TEXT,
            texto_extraido TEXT,
            data_registro TEXT
        );
        """)
        conn.commit()
    finally:
        conn.close()

    repo = DatabaseRepository(temp_db)

    # Dados de teste
    item = {
        'uuid': 'uuid-1',
        'caminho_origem': 'C:\\caminho\\arquivo1.txt',
        'nome_original': 'arquivo1.txt',
        'tamanho_bytes': 100,
        'hash_xxhash': 'hash1',
        'status': 'pendente_extracao',
        'data_criacao_sistema': 12345,
        'data_modificacao_sistema': 12345,
        'justificativa_classificacao': '',
        'eh_duplicado': 0
    }

    repo.insert_batch([item])

    # Verifica insercao
    conn = sqlite3.connect(temp_db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT uuid, tamanho_bytes, status FROM arquivos_processamento WHERE uuid='uuid-1'")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == 100
        assert row[2] == 'pendente_extracao'
    finally:
        conn.close()

    # Testa conflito (ON CONFLICT DO UPDATE)
    item_modificado = item.copy()
    item_modificado['tamanho_bytes'] = 200
    item_modificado['status'] = 'erro'  # Deve reverter para pendente_extracao no ON CONFLICT

    repo.insert_batch([item_modificado])

    conn = sqlite3.connect(temp_db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tamanho_bytes, status FROM arquivos_processamento WHERE uuid='uuid-1'")
        row = cursor.fetchone()
        assert row[0] == 200
        # O trigger ON CONFLICT do insert_batch do repositorio reverte status erro/quarentena para pendente_extracao
        assert row[1] == 'pendente_extracao'
    finally:
        conn.close()

def test_inventory_worker_execution(temp_dir, temp_db):
    """Verifica a integracao do InventoryWorker do Scanner ate o Banco de Dados."""
    # Criamos o banco temporario com a tabela
    conn = sqlite3.connect(temp_db)
    try:
        conn.execute("""
        CREATE TABLE arquivos_processamento (
            uuid TEXT PRIMARY KEY,
            caminho_origem TEXT UNIQUE,
            nome_original TEXT,
            tamanho_bytes INTEGER,
            hash_xxhash TEXT,
            status TEXT,
            data_criacao_sistema INTEGER,
            data_modificacao_sistema INTEGER,
            justificativa_classificacao TEXT,
            eh_duplicado INTEGER,
            motivo_falha TEXT,
            mensagem_erro TEXT,
            texto_extraido TEXT,
            data_registro TEXT
        );
        """)
        conn.commit()
    finally:
        conn.close()

    # Criamos arquivos para escanear
    file1 = temp_dir / "teste_worker.txt"
    file1.write_text("conteudo para o worker")

    worker = InventoryWorker(str(temp_dir), temp_db)
    total = worker.execute()

    assert total == 1

    # Verifica se o registro esta persistido no banco
    conn = sqlite3.connect(temp_db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT caminho_origem, hash_xxhash, status FROM arquivos_processamento")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == str(file1)
        assert row[1] == Hasher.compute_xxhash(str(file1))
        assert row[2] == 'pendente_extracao'
    finally:
        conn.close()
