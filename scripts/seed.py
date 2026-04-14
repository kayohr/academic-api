"""
Seed de dados realistas para o academic-api.
Uso: python scripts/seed.py
Idempotente: verifica existência antes de inserir.
"""

import os
import sys
import random
import bcrypt
from datetime import date, timedelta
from dotenv import load_dotenv
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.environ["DATABASE_URL"]
fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)


def conectar():
    return psycopg2.connect(DATABASE_URL)


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()


def cpf_aleatorio():
    nums = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        soma = sum((len(nums) + 1 - i) * n for i, n in enumerate(nums))
        digito = (soma * 10 % 11) % 10
        nums.append(digito)
    return "".join(map(str, nums))


def ja_existe(cur, tabela: str, campo: str, valor) -> bool:
    cur.execute(f"SELECT 1 FROM {tabela} WHERE {campo} = %s LIMIT 1", (valor,))
    return cur.fetchone() is not None


def seed_campus(cur):
    dados = [
        ("Campus Central", "São Paulo", "SP", "Av. Paulista, 1000", "(11) 3333-0000", "central@academic.edu"),
        ("Campus Norte", "Campinas", "SP", "Rua das Flores, 500", "(19) 4444-0001", "norte@academic.edu"),
    ]
    ids = []
    for nome, cidade, estado, end, tel, email in dados:
        if not ja_existe(cur, "campus", "nome", nome):
            cur.execute(
                "INSERT INTO campus (nome, cidade, estado, endereco, telefone, email) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (nome, cidade, estado, end, tel, email),
            )
            ids.append(cur.fetchone()[0])
            print(f"  [campus] {nome}")
        else:
            cur.execute("SELECT id FROM campus WHERE nome = %s", (nome,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_departamentos(cur, campus_ids):
    dados = [
        (campus_ids[0], "Ciência da Computação", "CC"),
        (campus_ids[0], "Engenharia de Software", "ES"),
        (campus_ids[1], "Sistemas de Informação", "SI"),
    ]
    ids = []
    for campus_id, nome, sigla in dados:
        if not ja_existe(cur, "departamento", "sigla", sigla):
            cur.execute(
                "INSERT INTO departamento (campus_id, nome, sigla) VALUES (%s,%s,%s) RETURNING id",
                (campus_id, nome, sigla),
            )
            ids.append(cur.fetchone()[0])
            print(f"  [departamento] {sigla}")
        else:
            cur.execute("SELECT id FROM departamento WHERE sigla = %s", (sigla,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_cursos(cur, dep_ids):
    dados = [
        (dep_ids[0], "Ciência da Computação", "CC001", "Bacharelado", "presencial", 8, 240),
        (dep_ids[1], "Engenharia de Software", "ES001", "Bacharelado", "presencial", 8, 240),
        (dep_ids[2], "Sistemas de Informação", "SI001", "Bacharelado", "presencial", 8, 200),
    ]
    ids = []
    for dep_id, nome, codigo, grau, modalidade, dur, cred in dados:
        if not ja_existe(cur, "curso", "codigo", codigo):
            cur.execute(
                "INSERT INTO curso (departamento_id, nome, codigo, grau, modalidade, duracao_semestres, creditos_necessarios) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (dep_id, nome, codigo, grau, modalidade, dur, cred),
            )
            ids.append(cur.fetchone()[0])
            print(f"  [curso] {codigo}")
        else:
            cur.execute("SELECT id FROM curso WHERE codigo = %s", (codigo,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_disciplinas(cur, dep_ids):
    disciplinas = [
        (dep_ids[0], "MAT001", "Cálculo I",            120, 6),
        (dep_ids[0], "MAT002", "Cálculo II",           120, 6),
        (dep_ids[0], "ALG001", "Álgebra Linear",        60, 4),
        (dep_ids[0], "POO001", "Prog. Orientada a Obj.",60, 4),
        (dep_ids[0], "EST001", "Estruturas de Dados",   60, 4),
        (dep_ids[1], "ENG001", "Eng. de Requisitos",    60, 4),
        (dep_ids[1], "TST001", "Testes de Software",    60, 4),
        (dep_ids[2], "BD001",  "Banco de Dados",        60, 4),
        (dep_ids[2], "RED001", "Redes de Computadores", 60, 4),
    ]
    ids = []
    for dep_id, codigo, nome, ch, cred in disciplinas:
        if not ja_existe(cur, "disciplina", "codigo", codigo):
            cur.execute(
                "INSERT INTO disciplina (departamento_id, codigo, nome, carga_horaria, creditos) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (dep_id, codigo, nome, ch, cred),
            )
            ids.append(cur.fetchone()[0])
            print(f"  [disciplina] {codigo}")
        else:
            cur.execute("SELECT id FROM disciplina WHERE codigo = %s", (codigo,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_prerequisitos(cur, disc_ids):
    # MAT002 requer MAT001; EST001 requer POO001
    pares = [(disc_ids[1], disc_ids[0]), (disc_ids[4], disc_ids[3])]
    for disc_id, pre_id in pares:
        cur.execute(
            "SELECT 1 FROM prerequisito WHERE disciplina_id=%s AND prerequisito_id=%s",
            (disc_id, pre_id),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO prerequisito (disciplina_id, prerequisito_id) VALUES (%s,%s)",
                (disc_id, pre_id),
            )
            print(f"  [prerequisito] {disc_id} requer {pre_id}")


def seed_grade(cur, curso_ids, disc_ids):
    grade = [
        (curso_ids[0], disc_ids[0], 1, "obrigatoria"),
        (curso_ids[0], disc_ids[1], 2, "obrigatoria"),
        (curso_ids[0], disc_ids[2], 1, "obrigatoria"),
        (curso_ids[0], disc_ids[3], 2, "obrigatoria"),
        (curso_ids[0], disc_ids[4], 3, "obrigatoria"),
    ]
    for curso_id, disc_id, periodo, tipo in grade:
        cur.execute(
            "SELECT 1 FROM grade_curricular WHERE curso_id=%s AND disciplina_id=%s",
            (curso_id, disc_id),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO grade_curricular (curso_id, disciplina_id, periodo, tipo) VALUES (%s,%s,%s,%s)",
                (curso_id, disc_id, periodo, tipo),
            )


def seed_professores(cur, dep_ids):
    titulacoes = ["mestre", "doutor", "especialista"]
    ids = []
    for i in range(6):
        cpf = cpf_aleatorio()
        siape = f"SIAPE{10000 + i}"
        if not ja_existe(cur, "professor", "siape", siape):
            nome = fake.name()
            email = f"prof{i+1}@academic.edu"
            cur.execute(
                "INSERT INTO professor (departamento_id, nome, cpf, email, siape, titulacao, regime) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (dep_ids[i % len(dep_ids)], nome, cpf, email, siape, random.choice(titulacoes), "40h"),
            )
            prof_id = cur.fetchone()[0]
            # Cria usuário vinculado
            cur.execute(
                "INSERT INTO usuario (email, senha_hash, role, professor_id) VALUES (%s,%s,%s,%s)",
                (email, hash_senha("Prof@123"), "professor", prof_id),
            )
            ids.append(prof_id)
            print(f"  [professor] {siape} — {email}")
        else:
            cur.execute("SELECT id FROM professor WHERE siape = %s", (siape,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_alunos(cur, curso_ids):
    ids = []
    ano_atual = date.today().year
    for i in range(20):
        cpf = cpf_aleatorio()
        matricula = f"{ano_atual}{str(i+1).zfill(4)}"
        if not ja_existe(cur, "aluno", "matricula", matricula):
            nome = fake.name()
            email = f"aluno{i+1}@academic.edu"
            cur.execute(
                "INSERT INTO aluno (curso_id, matricula, nome, cpf, email, semestre_ingresso) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (curso_ids[i % len(curso_ids)], matricula, nome, cpf, email, f"{ano_atual}/1"),
            )
            aluno_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO usuario (email, senha_hash, role, aluno_id) VALUES (%s,%s,%s,%s)",
                (email, hash_senha("Aluno@123"), "aluno", aluno_id),
            )
            ids.append(aluno_id)
            print(f"  [aluno] {matricula} — {email}")
        else:
            cur.execute("SELECT id FROM aluno WHERE matricula = %s", (matricula,))
            ids.append(cur.fetchone()[0])
    return ids


def seed_semestre(cur):
    ano, periodo = date.today().year, 1
    if not ja_existe(cur, "semestre", "ano", ano):
        cur.execute(
            "INSERT INTO semestre (ano, periodo, data_inicio, data_fim, data_limite_trancamento, status) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (ano, periodo, date(ano, 2, 1), date(ano, 6, 30), date(ano, 3, 31), "ativo"),
        )
        sem_id = cur.fetchone()[0]
        print(f"  [semestre] {ano}/{periodo}")
    else:
        cur.execute("SELECT id FROM semestre WHERE ano=%s AND periodo=%s", (ano, periodo))
        sem_id = cur.fetchone()[0]
    return sem_id


def seed_turmas(cur, disc_ids, prof_ids, sem_id):
    dias = ["segunda", "terca", "quarta", "quinta", "sexta"]
    ids = []
    for i, disc_id in enumerate(disc_ids[:6]):
        codigo = f"T{str(i+1).zfill(3)}"
        cur.execute("SELECT 1 FROM turma WHERE codigo=%s AND semestre_id=%s", (codigo, sem_id))
        if not cur.fetchone():
            horario = [{"dia": dias[i % 5], "hora_inicio": "08:00", "hora_fim": "10:00"}]
            cur.execute(
                "INSERT INTO turma (disciplina_id, professor_id, semestre_id, codigo, sala, horario, vagas, status) "
                "VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING id",
                (disc_id, prof_ids[i % len(prof_ids)], sem_id, codigo, f"Sala {101+i}",
                 str(horario).replace("'", '"'), 30, "em_andamento"),
            )
            ids.append(cur.fetchone()[0])
            print(f"  [turma] {codigo}")
        else:
            cur.execute("SELECT id FROM turma WHERE codigo=%s AND semestre_id=%s", (codigo, sem_id))
            ids.append(cur.fetchone()[0])
    return ids


def seed_matriculas(cur, aluno_ids, turma_ids):
    for aluno_id in aluno_ids[:10]:
        for turma_id in random.sample(turma_ids, k=min(3, len(turma_ids))):
            cur.execute(
                "SELECT 1 FROM matricula WHERE aluno_id=%s AND turma_id=%s",
                (aluno_id, turma_id),
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO matricula (aluno_id, turma_id, status) VALUES (%s,%s,'ativa')",
                    (aluno_id, turma_id),
                )
    print(f"  [matriculas] até {10 * 3} matrículas criadas")


def main():
    print("Conectando ao banco...")
    conn = conectar()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print("\n>> Campus")
        campus_ids = seed_campus(cur)

        print("\n>> Departamentos")
        dep_ids = seed_departamentos(cur, campus_ids)

        print("\n>> Cursos")
        curso_ids = seed_cursos(cur, dep_ids)

        print("\n>> Disciplinas")
        disc_ids = seed_disciplinas(cur, dep_ids)

        print("\n>> Pré-requisitos")
        seed_prerequisitos(cur, disc_ids)

        print("\n>> Grade curricular")
        seed_grade(cur, curso_ids, disc_ids)

        print("\n>> Professores")
        prof_ids = seed_professores(cur, dep_ids)

        print("\n>> Alunos")
        aluno_ids = seed_alunos(cur, curso_ids)

        print("\n>> Semestre")
        sem_id = seed_semestre(cur)

        print("\n>> Turmas")
        turma_ids = seed_turmas(cur, disc_ids, prof_ids, sem_id)

        print("\n>> Matrículas")
        seed_matriculas(cur, aluno_ids, turma_ids)

        conn.commit()
        print("\n✓ Seed concluído com sucesso!")
        print("  Admin: admin@academic.com / Admin@123")
        print("  Professores: prof1@academic.edu ... / Prof@123")
        print("  Alunos: aluno1@academic.edu ... / Aluno@123")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Erro durante o seed: {e}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
