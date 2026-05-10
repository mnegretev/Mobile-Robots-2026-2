#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# MASTER SCRIPT FOR PRACTICE 3 - COMPLETE AUTOMATION
#
# This script runs all experiments and generates comprehensive reports
#

import os
import sys
import subprocess
import json
import glob
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True,
                              capture_output=True, text=True)
        print(f"✅ {description} - COMPLETADO")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERROR: {e}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def load_latest_results():
    """Load the most recent results from both experiment types"""
    # Find latest automated experiments results
    automated_files = glob.glob("automated_experiments_results_*.json")
    if not automated_files:
        print("❌ No automated experiments results found")
        return None, None

    automated_file = max(automated_files, key=os.path.getctime)
    with open(automated_file, 'r') as f:
        automated_results = json.load(f)

    # Find latest binary experiments results
    binary_files = glob.glob("*binary_experiments_results_*.json")
    if not binary_files:
        print("❌ No binary experiments results found")
        return None, None

    binary_file = max(binary_files, key=os.path.getctime)
    with open(binary_file, 'r') as f:
        binary_results = json.load(f)

    return automated_results, binary_results

def generate_comparative_report(automated_results, binary_results):
    """Generate comparative analysis report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"comparative_report_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# PRÁCTICA 3: ANÁLISIS COMPARATIVO\n\n")
        f.write("**Estudiante:** Galicia Rioja Angel Daniel\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## RESUMEN EJECUTIVO\n\n")
        f.write("Este reporte compara los resultados de dos enfoques para el reconocimiento ")
        f.write("de dígitos escritos a mano:\n\n")
        f.write("1. **Enfoque Tradicional**: 10 clases separadas (784-100-10)\n")
        f.write("2. **Enfoque Binario**: Representación de 4 bits (784-100-4)\n\n")

        # Overall comparison
        automated_best = max(automated_results, key=lambda x: x['metrics']['accuracy'])
        binary_best = max(binary_results, key=lambda x: x['metrics']['accuracy'])

        f.write("## COMPARACIÓN GENERAL\n\n")
        f.write("| Enfoque | Mejor Precisión | Tiempo Promedio | Arquitectura |\n")
        f.write("|---------|----------------|-----------------|--------------|\n")
        f.write(f"| Tradicional | {automated_best['metrics']['accuracy']:.3f} | {automated_best['training_time']:.1f}s | {automated_best['config']['layers']} |\n")
        f.write(f"| Binario | {binary_best['metrics']['accuracy']:.3f} | {binary_best['training_time']:.1f}s | {binary_best['config']['layers']} |\n")
        f.write("\n")

        # Parameter analysis
        f.write("## ANÁLISIS POR PARÁMETROS\n\n")

        # Learning rate comparison
        f.write("### Impacto de la Tasa de Aprendizaje\n\n")
        lr_comparison = {}
        for lr in [0.5, 1.0, 3.0, 10.0]:
            automated_accs = [r['metrics']['accuracy'] for r in automated_results if r['config']['learning_rate'] == lr]
            binary_accs = [r['metrics']['accuracy'] for r in binary_results if r['config']['learning_rate'] == lr]

            if automated_accs and binary_accs:
                lr_comparison[lr] = {
                    'traditional': np.mean(automated_accs),
                    'binary': np.mean(binary_accs)
                }

        f.write("| Tasa Aprendizaje | Tradicional | Binario | Diferencia |\n")
        f.write("|------------------|-------------|---------|------------|\n")
        for lr, accs in lr_comparison.items():
            diff = accs['traditional'] - accs['binary']
            f.write(f"| {lr} | {accs['traditional']:.3f} | {accs['binary']:.3f} | {diff:+.3f} |\n")
        f.write("\n")

        # Epochs comparison
        f.write("### Impacto del Número de Épocas\n\n")
        epoch_comparison = {}
        for ep in [3, 10, 50, 100]:
            automated_accs = [r['metrics']['accuracy'] for r in automated_results if r['config']['epochs'] == ep]
            binary_accs = [r['metrics']['accuracy'] for r in binary_results if r['config']['epochs'] == ep]

            if automated_accs and binary_accs:
                epoch_comparison[ep] = {
                    'traditional': np.mean(automated_accs),
                    'binary': np.mean(binary_accs)
                }

        f.write("| Épocas | Tradicional | Binario | Diferencia |\n")
        f.write("|--------|-------------|---------|------------|\n")
        for ep, accs in epoch_comparison.items():
            diff = accs['traditional'] - accs['binary']
            f.write(f"| {ep} | {accs['traditional']:.3f} | {accs['binary']:.3f} | {diff:+.3f} |\n")
        f.write("\n")

        # Batch size comparison
        f.write("### Impacto del Tamaño del Lote\n\n")
        batch_comparison = {}
        for bs in [5, 10, 30, 100]:
            automated_accs = [r['metrics']['accuracy'] for r in automated_results if r['config']['batch_size'] == bs]
            binary_accs = [r['metrics']['accuracy'] for r in binary_results if r['config']['batch_size'] == bs]

            if automated_accs and binary_accs:
                batch_comparison[bs] = {
                    'traditional': np.mean(automated_accs),
                    'binary': np.mean(binary_accs)
                }

        f.write("| Tamaño Lote | Tradicional | Binario | Diferencia |\n")
        f.write("|-------------|-------------|---------|------------|\n")
        for bs, accs in batch_comparison.items():
            diff = accs['traditional'] - accs['binary']
            f.write(f"| {bs} | {accs['traditional']:.3f} | {accs['binary']:.3f} | {diff:+.3f} |\n")
        f.write("\n")

        f.write("## GRÁFICOS DE ANÁLISIS\n\n")
        f.write("### Clasificación de 10 Clases\n\n")
        f.write("![Precisión vs Tasa de Aprendizaje](automated_accuracy_vs_lr.png)\n")
        f.write("![Precisión vs Épocas](automated_accuracy_vs_epochs.png)\n")
        f.write("![Precisión vs Tamaño del Lote](automated_accuracy_vs_batch_size.png)\n")
        f.write("![Distribución de Precisión](automated_accuracy_boxplot.png)\n\n")
        f.write("### Clasificación Binaria\n\n")
        f.write("![Precisión vs Tasa de Aprendizaje](binary_accuracy_vs_lr.png)\n")
        f.write("![Precisión vs Épocas](binary_accuracy_vs_epochs.png)\n")
        f.write("![Precisión vs Tamaño del Lote](binary_accuracy_vs_batch_size.png)\n")
        f.write("![Distribución de Precisión](binary_accuracy_boxplot.png)\n\n")

        f.write("## CONCLUSIONES\n\n")

        # Determine which approach is better
        traditional_avg = np.mean([r['metrics']['accuracy'] for r in automated_results])
        binary_avg = np.mean([r['metrics']['accuracy'] for r in binary_results])

        f.write(f"**Precisión promedio - Tradicional:** {traditional_avg:.3f}\n")
        f.write(f"**Precisión promedio - Binario:** {binary_avg:.3f}\n\n")

        if traditional_avg > binary_avg:
            f.write("El enfoque tradicional muestra un mejor desempeño general ")
            f.write(f"con una diferencia de {traditional_avg - binary_avg:.3f} en precisión.\n\n")
        else:
            f.write("El enfoque binario muestra un mejor desempeño general ")
            f.write(f"con una diferencia de {binary_avg - traditional_avg:.3f} en precisión.\n\n")

        f.write("### Recomendaciones\n\n")
        f.write("- **Para máxima precisión**: Utilizar el enfoque tradicional con 10 clases separadas\n")
        f.write("- **Para eficiencia**: Considerar el enfoque binario cuando se requiera menor complejidad\n")
        f.write("- **Optimización**: Los parámetros óptimos varían según el enfoque utilizado\n\n")

        f.write("---\n\n")
        f.write("*Reporte comparativo generado automáticamente*\n")

    print(f"📄 Comparative report generated: {filename}")
    return filename

def main():
    print("PRACTICE 3 - COMPLETE AUTOMATION SCRIPT")
    print("=" * 60)
    print("Student: Galicia Rioja Angel Daniel")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if dataset exists
    dataset_path = "../dataset"
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at {dataset_path}")
        print("Please ensure the dataset is available before running experiments.")
        return

    # Check if required data files exist
    data_files = [f"data{i}" for i in range(10)]
    missing_files = []
    for filename in data_files:
        if not os.path.exists(os.path.join(dataset_path, filename)):
            missing_files.append(filename)

    if missing_files:
        print(f"❌ Missing data files: {missing_files}")
        print("Please ensure all dataset files are present.")
        return

    # Run 10-class experiments
    success1, output1 = run_command("python3 automated_experiments.py", "Running 10-class digit classification experiments")
    if not success1:
        print("Failed to run 10-class experiments")
        return

    # Run binary label experiments
    success2, output2 = run_command("python3 binary_experiments.py", "Running binary label digit classification experiments")
    if not success2:
        print("Failed to run binary experiments")
        return

    # Generate comparative report
    print("\n🔄 Generating comparative analysis report")
    automated_results, binary_results = load_latest_results()
    if automated_results and binary_results:
        comparative_file = generate_comparative_report(automated_results, binary_results)
        print(f"✅ Comparative report generated: {comparative_file}")
    else:
        print("❌ Failed to load results for comparative analysis")

    # Generate graphs
    success3, output3 = run_command("python3 generate_graphs.py", "Generating analysis graphs")
    if not success3:
        print("Failed to generate graphs")
    else:
        print("✅ Graphs generated successfully")

    print("\n🎉 ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print("Generated files:")
    print("- automated_experiments_report_*.md")
    print("- binary_experiments_report_*.md")
    print("- comparative_report_*.md")
    print("- Results saved in JSON format")
    print("- Analysis graphs (*.png)")

if __name__ == "__main__":
    import numpy as np
    main()
