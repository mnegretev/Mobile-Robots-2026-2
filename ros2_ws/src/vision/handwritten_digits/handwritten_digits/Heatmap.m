% =========================================================================
% ROBOTS MÓVILES (2026-2) - REPORTE PRÁCTICA 03
% Autor: Oscar Saldivar Pantoja
% Graficación de Mapas de Calor Globales (Modelo Binario)
% =========================================================================
clear; clc; close all;

% 1. Leer el archivo de datos binarios
if exist('resultados_binarios.csv', 'file')
    data_bin = readtable('resultados_binarios.csv');
else
    error('El archivo resultados_binarios.csv no se encuentra en el directorio actual.');
end

% 2. Identificar los valores únicos de los parámetros
lotes = unique(data_bin.BatchSize);

% 3. Configurar la figura principal para los subplots binarios
figure('Name', 'Mapas de Calor - Modelo Binario', 'NumberTitle', 'off', 'Position', [150, 150, 1100, 850]);
sgtitle('Análisis de Tasa de Éxito (%) - Modelo Binario ', 'FontSize', 16, 'FontWeight', 'bold');

% 4. Ciclo para generar un Heatmap por cada Batch Size (Modo Binario)
for i = 1:numel(lotes)
    subplot(2, 2, i);
    
    % Filtrar los datos correspondientes al lote binario actual
    data_filtrada = data_bin(data_bin.BatchSize == lotes(i), :);
    
    % Crear el mapa de calor
    h = heatmap(data_filtrada, 'LearningRate', 'Epochs', 'ColorVariable', 'SuccessRate___');
    
    % Personalización del Heatmap
    h.Title = ['Batch Size = ' num2str(lotes(i))];
    h.XLabel = 'Tasa de Aprendizaje (\eta)';
    h.YLabel = 'Épocas de Entrenamiento';
    h.Colormap = hot; % Paleta térmica de tonos fuego, excelente para reportes visuales
    
    % Mantener la consistencia en el rango de éxito
    caxis([0 100]); 
end