"use client";

import { useState } from "react";

const EXEMPLOS = [
  { rotulo: "📅 Agendar", texto: "Oi! Queria marcar banho e tosa pro Bob na sexta à tarde. Tem horário?" },
  { rotulo: "🩺 Sintomas", texto: "Minha gata Luna está vomitando desde ontem e não quer comer nada. O que eu faço?" },
  { rotulo: "💬 Dúvida", texto: "Vocês atendem coelhos? E funcionam no sábado?" },
  { rotulo: "💉 Vacina", texto: "Quando é o reforço da V10 do Thor? E já saiu o resultado do hemograma?" },
  { rotulo: "😿 Reclamação", texto: "Esperei mais de uma hora ontem e ninguém me deu satisfação. Quero falar com o responsável." },
  { rotulo: "💰 Financeiro", texto: "Quanto custa a castração de uma gata? Dá pra parcelar no cartão?" },
];

const CATEGORIAS = {
  "Agendamento": { emoji: "📅", cor: "#ffe9c7" },
  "Sintomas / possível urgência": { emoji: "🩺", cor: "#ffd9de" },
  "Dúvidas sobre serviços": { emoji: "💬", cor: "#dff3ff" },
  "Vacinação e exames": { emoji: "💉", cor: "#e3f7ee" },
  "Reclamações": { emoji: "😿", cor: "#efe7ff" },
  "Financeiro": { emoji: "💰", cor: "#fff3c4" },
};

const URGENCIAS = { baixa: "Baixa 🌿", media: "Média 🌼", alta: "Alta 🔥", emergencia: "Emergência 🚨" };

export default function Home() {
  const [remetente, setRemetente] = useState("");
  const [canal, setCanal] = useState("site");
  const [mensagem, setMensagem] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [resultado, setResultado] = useState(null);

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setResultado(null);

    if (mensagem.trim().length < 3) {
      setErro("Escreva uma mensagem um pouquinho maior.");
      return;
    }

    setCarregando(true);
    try {
      const resposta = await fetch("/api/mensagem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mensagem: mensagem.trim(),
          canal,
          remetente: remetente.trim() || null,
        }),
      });
      const dados = await resposta.json();

      if (!resposta.ok) {
        const detalhe = typeof dados.detail === "string" ? dados.detail : "dados inválidos";
        throw new Error(detalhe);
      }
      if (!dados.classificacao) {
        throw new Error("A resposta da API chegou sem a classificação.");
      }
      setResultado(dados);
    } catch (e) {
      setErro(e.message || "Algo deu errado.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main className="container">
      <Patinhas />

      <header className="cabecalho">
        <div className="mascote" aria-hidden="true">🐶</div>
        <h1>
          PetFlow <small>AI</small>
        </h1>
        <p>Conta pra gente o que seu pet precisa 💕</p>
      </header>

      <form className="cartao" onSubmit={enviar}>
        <div className="linha">
          <div>
            <label htmlFor="remetente">Seu nome</label>
            <input id="remetente" value={remetente} onChange={(e) => setRemetente(e.target.value)} placeholder="Ex.: Maria" maxLength={80} />
          </div>
          <div>
            <label htmlFor="canal">Por onde você fala com a gente?</label>
            <select id="canal" value={canal} onChange={(e) => setCanal(e.target.value)}>
              <option value="site">Site</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="instagram">Instagram</option>
              <option value="email">E-mail</option>
            </select>
          </div>
        </div>

        <label htmlFor="mensagem">Sua mensagem</label>
        <textarea
          id="mensagem"
          value={mensagem}
          onChange={(e) => setMensagem(e.target.value)}
          placeholder="Ex.: Oi! A Mel está espirrando muito desde ontem..."
          maxLength={2000}
        />
        <div className="contador">{mensagem.length}/2000</div>

        <p className="dica">Sem ideia? Experimente um exemplo:</p>
        <div className="chips">
          {EXEMPLOS.map((ex) => (
            <button key={ex.rotulo} type="button" className="chip" onClick={() => setMensagem(ex.texto)}>
              {ex.rotulo}
            </button>
          ))}
        </div>

        <button className="botao" type="submit" disabled={carregando}>
          {carregando ? "Enviando..." : "Enviar mensagem 🐾"}
        </button>

        {carregando && (
          <div className="carregando">
            <div className="pegadas">
              <span>🐾</span>
              <span>🐾</span>
              <span>🐾</span>
              <span>🐾</span>
            </div>
            <p>Farejando sua mensagem...</p>
          </div>
        )}
      </form>

      {erro && <div className="erro">🙀 {erro}</div>}

      {resultado && <Resultado dados={resultado} />}

      <footer>Feito com 💕 para tutores e seus bichinhos · PetFlow AI (projeto fictício)</footer>
    </main>
  );
}

function Resultado({ dados }) {
  const c = dados.classificacao;
  const e = dados.encaminhamento;
  const visual = CATEGORIAS[c.categoria] ?? { emoji: "🐾", cor: "#f4eefc" };
  const nivel = (e.prioridade ?? "").slice(0, 2).toLowerCase();
  const pet = [c.nome_pet, c.especie].filter(Boolean).join(" · ") || "Não informado";
  const n8n = dados.automacao;

  return (
    <section className="cartao resultado" aria-live="polite">
      <div className="topo">
        <div className="emoji" style={{ background: visual.cor }}>
          {visual.emoji}
        </div>
        <div>
          <h2>{c.categoria}</h2>
          <p>
            Encaminhado para <strong>{e.setor}</strong>
          </p>
        </div>
      </div>

      <div className="selos">
        <span className={`selo ${nivel}`}>{e.prioridade}</span>
        {e.alerta_veterinario && <span className="selo alerta">🚑 Equipe veterinária avisada</span>}
        {e.revisao_humana && <span className="selo revisao">👀 Vai passar por revisão humana</span>}
        <span className="selo">Confiança {Math.round((c.confianca ?? 0) * 100)}%</span>
      </div>

      <div className="info">
        <div>
          <span>Pet</span>
          <b>{pet}</b>
        </div>
        <div>
          <span>Urgência</span>
          <b>{URGENCIAS[c.urgencia] ?? c.urgencia}</b>
        </div>
      </div>

      <div className="resumo">
        <span>Resumo</span>
        <div>{c.resumo}</div>
        {c.sintomas?.length > 0 && (
          <div className="sintomas">
            {c.sintomas.map((s) => (
              <em key={s}>{s}</em>
            ))}
          </div>
        )}
      </div>

      <span className="rotulo">Resposta para você 💌</span>
      <div className="bolha">{c.resposta_sugerida}</div>

      <Automacao n8n={n8n} />

      <p className="rodape">
        Interface → API ({dados.origem ?? "?"}) → n8n · protocolo {String(dados.id ?? "").slice(0, 8)}
      </p>
    </section>
  );
}

function Automacao({ n8n }) {
  if (!n8n) return null;

  if (!n8n.enviado) {
    return (
      <div className="automacao falhou">
        <span className="rotulo">Automação n8n</span>
        <b>⚠️ A mensagem foi classificada, mas não chegou ao n8n.</b>
        <p>{n8n.detalhe}</p>
      </div>
    );
  }

  const r = n8n.resposta ?? {};
  return (
    <div className="automacao ok">
      <span className="rotulo">Automação n8n</span>
      <b>🤖 Atendimento {r.status ?? "encaminhado"}{r.fila_destino ? ` para a fila "${r.fila_destino}"` : ""}</b>
      {r.ticket && <p className="ticket">{r.ticket}</p>}
      {r.alerta && <p className="alerta-n8n">{r.alerta}</p>}
    </div>
  );
}

function Patinhas() {
  const posicoes = [
    { top: "8%", left: "6%", rotate: -20 },
    { top: "30%", right: "7%", rotate: 25 },
    { top: "62%", left: "4%", rotate: 10 },
    { top: "80%", right: "12%", rotate: -30 },
    { top: "45%", left: "48%", rotate: 40 },
  ];
  return (
    <div className="patinhas" aria-hidden="true">
      {posicoes.map(({ rotate, ...pos }, i) => (
        <span key={i} style={{ ...pos, transform: `rotate(${rotate}deg)` }}>
          🐾
        </span>
      ))}
    </div>
  );
}
