def levenshtein_distance(s1, s2):
    """Calcula la distancia de Levenshtein entre dos cadenas"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def similarity_percentage(s1, s2):
    """Calcula el porcentaje de similitud entre dos cadenas"""
    distance = levenshtein_distance(s1.lower(), s2.lower())
    max_length = max(len(s1), len(s2))
    return ((max_length - distance) / max_length) * 100

def find_similar_matches(file1_path, file2_path, similarity_threshold=80):
    try:
        # Leer los archivos
        with open(file1_path, 'r', encoding='utf-8') as f1:
            lines1 = [line.strip() for line in f1 if line.strip()]
        
        with open(file2_path, 'r', encoding='utf-8') as f2:
            lines2 = [line.strip() for line in f2 if line.strip()]
        
        # Encontrar coincidencias similares
        similar_matches = []
        for line1 in lines1:
            for line2 in lines2:
                similarity = similarity_percentage(line1, line2)
                if similarity >= similarity_threshold:
                    similar_matches.append((line1, line2, similarity))
        
        if similar_matches:
            print("\nCoincidencias similares encontradas:")
            print("====================================")
            for line1, line2, similarity in sorted(similar_matches, key=lambda x: x[2], reverse=True):
                print(f"\nSimilitud: {similarity:.2f}%")
                print(f"Pedido: {line1}")
                print(f"En Bodega: {line2}")
            print(f"\nTotal de coincidencias similares: {len(similar_matches)}")
        else:
            print("\nNo se encontraron coincidencias similares entre los archivos.")
            
    except FileNotFoundError as e:
        print(f"\nError: No se pudo encontrar el archivo: {str(e).split(']')[1]}")
    except Exception as e:
        print(f"\nError inesperado: {e}")

def main():
    print("\nComparador de textos similares")
    print("=============================")
    
    # Solicitar nombres de archivos y umbral de similitud
    file1 = input("\nIngrese el nombre del primer archivo (con extensión): ")
    file2 = input("Ingrese el nombre del segundo archivo (con extensión): ")
    
    try:
        threshold = float(input("Ingrese el porcentaje mínimo de similitud (1-100) [predeterminado=70]: ") or 70)
        threshold = max(1, min(100, threshold))  # Asegurar que esté entre 1 y 100
    except ValueError:
        print("Valor inválido, usando 70% como umbral predeterminado.")
        threshold = 70
    
    # Realizar la comparación
    find_similar_matches(file1, file2, threshold)

if __name__ == "__main__":
    main()