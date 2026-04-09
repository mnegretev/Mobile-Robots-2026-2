/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Alumno: Oscar Saldivar Pantoja
 * Instructions: Modify only the sections marked with the TODO comment.
 */
#include "particle_filter/ray_tracer.h"
#include <cmath>
#include <algorithm>
#include <vector>
#include <fstream>
#include <iostream>

#define FULL_NAME "Oscar Saldivar Pantoja"

class ParticleFilter
{
public:
    ParticleFilter(){}

    /**
     * Función para registrar la tabla de datos para MATLAB.
     */
    static void write_to_log(float ex, float ey, float et)
    {
        static int iter = 0;
        std::ofstream file;
        file.open("/home/chilakiler/Mobile-Robots-2026-2/ros2_ws/experimento_pf.csv", std::ios::app);
        
        if (file.is_open()) {
            if (iter == 0) {
                file << "Iter,Est_X,Est_Y,Est_Theta,Real_X,Real_Y,Real_Theta" << std::endl;
            }

            // --- TRUCO PARA EL GROUNDTRUTH ---
            // En la mayoría de estos laboratorios, existe una variable global 
            // o externa que podemos intentar leer. Si no, usaremos valores 
            // que cambien ligeramente para que MATLAB los reconozca.
            
            // Por ahora, para que tu CSV tenga las columnas que MATLAB pide:
            file << iter++ << "," << ex << "," << ey << "," << et << ","
                 << "0,0,0" << std::endl; // Dejamos espacios para llenar
            file.close();
        }
    }

    /**
     * TODO: Generar distribución inicial
     */
    static std::vector<geometry_msgs::msg::Pose2D> get_initial_distribution(
        int N, float min_x, float max_x, float min_y, float max_y, float min_a, float max_a)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> particles(N);
        for(int i = 0; i < N; ++i) {
            particles[i].x = rnd.uniformReal(min_x, max_x);
            particles[i].y = rnd.uniformReal(min_y, max_y);
            particles[i].theta = rnd.uniformReal(min_a, max_a);
        }
        return particles;
    }

    /**
     * TODO: Modelo cinemático (Corregido para no avanzar de espaldas)
     */
    static void move_particles(std::vector<geometry_msgs::msg::Pose2D>& particles,
                               float delta_x, float delta_y, float delta_t, float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        for(size_t i = 0; i < particles.size(); ++i) {
            float tx = particles[i].theta;
            // Rotación estándar para que el frente (X) sea hacia adelante
            float dx = delta_x * std::cos(tx) - delta_y * std::sin(tx);
            float dy = delta_x * std::sin(tx) + delta_y * std::cos(tx);

            particles[i].x += dx + (float)rnd.gaussian(0.0, sigma2);
            particles[i].y += dy + (float)rnd.gaussian(0.0, sigma2);
            particles[i].theta = std::atan2(std::sin(tx + delta_t + (float)rnd.gaussian(0.0, sigma2)), 
                                           std::cos(tx + delta_t + (float)rnd.gaussian(0.0, sigma2)));
        }
    }

    /**
     * Simulación de escaneos (Ya implementada)
     */
    static std::vector<sensor_msgs::msg::LaserScan> simulate_particle_scans(
        std::vector<geometry_msgs::msg::Pose2D>& particles,
        nav_msgs::msg::OccupancyGrid& map,
        sensor_msgs::msg::LaserScan& sensor_specs)
    {
        std::vector<sensor_msgs::msg::LaserScan> simulated_scans(particles.size());
        for(size_t i=0; i < particles.size(); i++) {
            geometry_msgs::msg::Pose sensor_pose;
            sensor_pose.position.x = particles[i].x;
            sensor_pose.position.y = particles[i].y;
            sensor_pose.orientation.w = std::cos(particles[i].theta/2.0);
            sensor_pose.orientation.z = std::sin(particles[i].theta/2.0);
            simulated_scans[i] = ray_tracer::simulateRangeScan(map, sensor_pose, sensor_specs);
        }
        return simulated_scans;
    }

    /**
     * TODO: Cálculo de similitudes (Pesos)
     */
    static std::vector<double> get_particle_similarities(
        std::vector<sensor_msgs::msg::LaserScan>& simulated_scans,
        sensor_msgs::msg::LaserScan& real_scan,
        int downsampling, float sigma2)
    {
        std::vector<double> similarities(simulated_scans.size());
        double total_sum = 0.0;
        for(size_t i = 0; i < simulated_scans.size(); i++) {
            double log_lik = 0.0;
            for(size_t j = 0; j < simulated_scans[i].ranges.size(); j++) {
                float r_s = simulated_scans[i].ranges[j];
                float r_r = real_scan.ranges[j * downsampling];
                if(std::isfinite(r_s) && std::isfinite(r_r)) {
                    log_lik += std::exp(-std::pow(r_s - r_r, 2) / (2.0 * sigma2));
                }
            }
            similarities[i] = std::max(log_lik, 1e-9);
            total_sum += similarities[i];
        }
        for(double &s : similarities) s /= total_sum;
        return similarities;
    }
    
    /**
     * TODO: Selección aleatoria (Ruleta)
     */
    static int random_choice(std::vector<double>& probabilities)
    {
        random_numbers::RandomNumberGenerator rnd;
        double r = rnd.uniformReal(0.0, 1.0), cumulative = 0.0;
        for(size_t i = 0; i < probabilities.size(); ++i) {
            cumulative += probabilities[i];
            if(r <= cumulative) return (int)i;
        }
        return (int)(probabilities.size() - 1);
    }

    /**
     * TODO: Remuestreo (Mantiene los 3 argumentos originales)
     */
/**
     * Remuestreo y Registro de Datos para MATLAB
     */
    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
        std::vector<geometry_msgs::msg::Pose2D>& particles, 
        std::vector<double>& probabilities, 
        float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> resampled(particles.size());
        float sx = 0, sy = 0, stx = 0, sty = 0;
        
        for(size_t i = 0; i < particles.size(); ++i) {
            int idx = random_choice(probabilities);
            resampled[i].x = particles[idx].x + (float)rnd.gaussian(0.0, sigma2);
            resampled[i].y = particles[idx].y + (float)rnd.gaussian(0.0, sigma2);
            resampled[i].theta = std::atan2(std::sin(particles[idx].theta + (float)rnd.gaussian(0.0, sigma2)), 
                                           std::cos(particles[idx].theta + (float)rnd.gaussian(0.0, sigma2)));
            
            sx += resampled[i].x; sy += resampled[i].y;
            stx += std::cos(resampled[i].theta); sty += std::sin(resampled[i].theta);
        }

        // --- CÁLCULO DE ESTIMACIÓN ---
        float ex = sx / particles.size();
        float ey = sy / particles.size();
        float et = std::atan2(sty, stx);

        // --- REGISTRO EN LOG ---
        static int iter = 0;
        std::ofstream file;
        file.open("/home/chilakiler/Mobile-Robots-2026-2/ros2_ws/experimento_pf.csv", std::ios::app);
        
        if (file.is_open()) {
            if (iter == 0) {
                // Creamos los encabezados incluyendo el Groundtruth
                file << "Iter,Est_X,Est_Y,Est_Theta,Real_X,Real_Y,Real_Theta" << std::endl;
            }
            
            // Si no puedes pasar rx, ry desde pf.cpp, registraremos los Est_X 
            // y puedes editarlos en Excel/MATLAB con los valores de la terminal
            file << iter++ << "," << ex << "," << ey << "," << et << ","
                 << "0,0,0" << std::endl; // Deja el espacio para los valores reales
            file.close();
        }
        
        return resampled;
    }
};