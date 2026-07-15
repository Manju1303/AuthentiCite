import uuid
import json
from backend.app.database import create_paper, add_sections, get_db_connection
from backend.app.similarity.analyzer import save_section_embeddings

def seed_database():
    print("Seeding academic papers for similarity testing...")
    
    # Paper 1: Transformer Models
    p1_id = "paper_transformer_seed_001"
    create_paper(p1_id, "A_Survey_on_Transformer_Models.pdf", "pdf")
    
    p1_sections = [
        {
            "id": "p1_sec_0",
            "paper_id": p1_id,
            "section_name": "Title/Abstract",
            "original_text": "A Survey on Transformer Models in Natural Language Processing",
            "layout_metadata": {"type": "paragraph", "style": "Title"}
        },
        {
            "id": "p1_sec_1",
            "paper_id": p1_id,
            "section_name": "Abstract",
            "original_text": "Transformer architectures have revolutionized natural language processing tasks by utilizing self-attention mechanisms to capture long-range dependencies in sequence data. This paper presents a comprehensive review of transformer variants and their application across diverse NLP benchmarks.",
            "layout_metadata": {"type": "paragraph"}
        },
        {
            "id": "p1_sec_2",
            "paper_id": p1_id,
            "section_name": "Introduction",
            "original_text": "Since their introduction by Vaswani et al. in 2017, transformer models have become the dominant architecture in deep learning for language representation. Unlike traditional recurrent neural networks, transformers process sequence tokens in parallel, significantly accelerating training times and enabling the training of extremely large language models.",
            "layout_metadata": {"type": "paragraph"}
        },
        {
            "id": "p1_sec_3",
            "paper_id": p1_id,
            "section_name": "Methodology",
            "original_text": "The core of the transformer architecture lies in the multi-head self-attention mechanism. This mechanism projects input vectors into query, key, and value spaces, computing attention weights as a scaled dot-product. Multiple attention heads allow the model to jointly attend to information from different representation subspaces at different positions.",
            "layout_metadata": {"type": "paragraph"}
        }
    ]
    add_sections(p1_sections)
    save_section_embeddings(p1_id, p1_sections)
    
    # Paper 2: Neural Networks
    p2_id = "paper_nn_seed_002"
    create_paper(p2_id, "Introduction_to_Neural_Networks.docx", "docx")
    
    p2_sections = [
        {
            "id": "p2_sec_0",
            "paper_id": p2_id,
            "section_name": "Title/Abstract",
            "original_text": "Introduction to Artificial Neural Networks and Backpropagation Algorithms",
            "layout_metadata": {"type": "paragraph", "style": "Title"}
        },
        {
            "id": "p2_sec_1",
            "paper_id": p2_id,
            "section_name": "Introduction",
            "original_text": "Artificial neural networks are computational systems inspired by the biological neural structures of the human brain. These systems learn to perform tasks by analyzing labeled examples, adjusting interconnecting weights through optimization algorithms to map inputs to desired outputs.",
            "layout_metadata": {"type": "paragraph"}
        },
        {
            "id": "p2_sec_2",
            "paper_id": p2_id,
            "section_name": "Methodology",
            "original_text": "The backpropagation algorithm is the primary method for training multi-layer perceptrons. It computes the gradient of the loss function with respect to each network weight using the chain rule of calculus. These gradients are then used by gradient descent optimizers to update the weights, minimizing prediction error over successive training epochs.",
            "layout_metadata": {"type": "paragraph"}
        }
    ]
    add_sections(p2_sections)
    save_section_embeddings(p2_id, p2_sections)
    
    # Mark status as parsed so they appear as complete in papers list
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE papers SET status = 'parsed' WHERE id IN (?, ?)", (p1_id, p2_id))
    conn.commit()
    conn.close()
    
    print("Seeding completed successfully!")

if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    db_conn = get_db_connection()
    # Call init_db first
    from backend.app.database import init_db
    init_db()
    seed_database()
