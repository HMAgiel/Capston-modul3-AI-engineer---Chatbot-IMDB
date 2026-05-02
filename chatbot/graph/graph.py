from langgraph.graph import StateGraph, START, END
from chatbot.graph.state import AgentState
from chatbot.graph.agent import supervisor_agent, Data_agent, SQL_agent, RAG_agent, OMDB_agent, Agregasi_agent, basic_agent


workflow = StateGraph(AgentState)

workflow.add_node("supervisor_agent", supervisor_agent)
workflow.add_node("basic_agent", basic_agent)
workflow.add_node("Data_agent", Data_agent)
workflow.add_node("SQL_agent", SQL_agent)
workflow.add_node("RAG_agent", RAG_agent)
workflow.add_node("OMDB_agent", OMDB_agent)
workflow.add_node("Agregasi_agent", Agregasi_agent)

workflow.add_edge(START, "supervisor_agent")

workflow.add_conditional_edges(
    "supervisor_agent",
    lambda state: state["next_worker"],
    {
        "basic_agent": "basic_agent",
        "Data_agent": "Data_agent"
    }
)

workflow.add_edge("basic_agent", END)

workflow.add_conditional_edges(
    "Data_agent",
    lambda state: state["data_worker"],
    {
        "SQL_agent": "SQL_agent",
        "RAG_agent": "RAG_agent",
        "OMDB_agent": "OMDB_agent",
        "Agregasi_agent": "Agregasi_agent"
    }
)

workflow.add_edge("SQL_agent", "Data_agent")
workflow.add_edge("RAG_agent", "Data_agent")
workflow.add_edge("OMDB_agent", "Data_agent")

workflow.add_edge("Agregasi_agent", END)

app = workflow.compile()

if __name__ == "__main__":
    
    def simpan_grafik_ke_file(app):
        print("Menghasilkan visualisasi grafik LangGraph...")
        try:
            # Menarik data grafik dalam bentuk byte PNG menggunakan format Mermaid
            gambar_bytes = app.get_graph().draw_mermaid_png()
            
            # Menyimpan byte tersebut menjadi file fisik bernama 'arsitektur_agen.png'
            nama_file = "arsitektur_agen.png"
            with open(nama_file, "wb") as f:
                f.write(gambar_bytes)
                
            print(f"✅ Grafik berhasil disimpan! Silakan buka file '{nama_file}' di foldermu.")
        
        except Exception as e:
            print(f"❌ Gagal membuat gambar. Pastikan koneksi internet aktif (karena LangGraph menggunakan API Mermaid). Error: {e}")

    # Panggil fungsinya
    simpan_grafik_ke_file(app)