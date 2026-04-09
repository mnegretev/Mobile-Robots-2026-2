/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Full Name: Gonzalez Fernandez Jonathan Uriel
 */
#include "particle_filter/ray_tracer.h"
#include <cmath>
#include <algorithm>

#define FULL_NAME "Gonzalez Fernandez Jonathan Uriel"

class ParticleFilter
{
public:
    ParticleFilter(){}

    static std::vector<geometry_msgs::msg::Pose2D> get_initial_distribution(
        int N, float min_x, float max_x, float min_y, float max_y, float min_a, float max_a)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> particles(N);

        for(int i = 0; i < N; i++)
        {
            particles[i].x     = rnd.uniformReal(min_x, max_x);
            particles[i].y     = rnd.uniformReal(min_y, max_y);
            particles[i].theta = rnd.uniformReal(min_a, max_a);
        }
        return particles;
    }

    static void move_particles(std::vector<geometry_msgs::msg::Pose2D>& particles,
                   float delta_x, float delta_y, float delta_t, float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        for(size_t i = 0; i < particles.size(); i++)
        {
            float theta_i = particles[i].theta;
            
            particles[i].x     += delta_x * cos(theta_i) - delta_y * sin(theta_i) + rnd.gaussian(0, sigma2);
            particles[i].y     += delta_x * sin(theta_i) + delta_y * cos(theta_i) + rnd.gaussian(0, sigma2);
            particles[i].theta += delta_t + rnd.gaussian(0, sigma2);
            
            // Mantener el ángulo en el rango válido
            particles[i].theta = atan2(sin(particles[i].theta), cos(particles[i].theta));
        }
    }

    static std::vector<sensor_msgs::msg::LaserScan> simulate_particle_scans(
        std::vector<geometry_msgs::msg::Pose2D>& particles,
        nav_msgs::msg::OccupancyGrid& map,
        sensor_msgs::msg::LaserScan& sensor_specs)
    {
        std::vector<sensor_msgs::msg::LaserScan> simulated_scans(particles.size());
        for(size_t i=0; i < particles.size(); i++)
        {
            geometry_msgs::msg::Pose sensor_pose;
            sensor_pose.position.x    = particles[i].x;
            sensor_pose.position.y    = particles[i].y;
            sensor_pose.orientation.w = cos(particles[i].theta / 2.0);
            sensor_pose.orientation.z = sin(particles[i].theta / 2.0);
            
            simulated_scans[i] = ray_tracer::simulateRangeScan(map, sensor_pose, sensor_specs);
        }
        return simulated_scans;
    }

    static std::vector<double> get_particle_similarities(
        std::vector<sensor_msgs::msg::LaserScan>& simulated_scans,
        sensor_msgs::msg::LaserScan& real_scan,
        int downsampling, float sigma2)
    {
        std::vector<double> similarities(simulated_scans.size());
        double total_sum = 0.0;
        
        // Evitar división por cero si llega un sigma2 igual a 0
        float s2 = std::max(sigma2, 0.0001f);

        for(size_t i = 0; i < simulated_scans.size(); i++) {
            double error_sum = 0.0;
            int count = 0;
            
            for(size_t j = 0; j < simulated_scans[i].ranges.size(); j += downsampling) {
                if(j >= real_scan.ranges.size()) break;
                float r_sim = simulated_scans[i].ranges[j];
                float r_real = real_scan.ranges[j];

                // Solo evaluar lecturas finitas (ignorar NaN o Infinitos)
                if(std::isfinite(r_sim) && std::isfinite(r_real)) {
                    double diff = r_real - r_sim;
                    error_sum += diff * diff; // Numerador: (z - z_sim)^2
                    count++;
                }
            }

            if(count > 0) {
                // Implementación exacta de la Ecuación 7 del PDF
                similarities[i] = std::exp(-error_sum / (2.0 * s2));
            } else {
                similarities[i] = 0.0;
            }
            total_sum += similarities[i];
        }

        // Normalización
        if(total_sum > 1e-9) {
            for(double &s : similarities) s /= total_sum;
        } else {
            for(double &s : similarities) s = 1.0 / similarities.size();
        }
        return similarities;
    }

    static int random_choice(std::vector<double>& probabilities)
    {
        random_numbers::RandomNumberGenerator rnd;
        double r = rnd.uniformReal(0.0, 1.0);
        double cumulative_sum = 0.0;

        for(size_t i = 0; i < probabilities.size(); i++) {
            cumulative_sum += probabilities[i];
            if(r <= cumulative_sum) return i;
        }
        return probabilities.size() - 1;
    }

    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
        std::vector<geometry_msgs::msg::Pose2D>& particles, 
        std::vector<double>& probabilities, float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> resampled(particles.size());

        for(size_t i = 0; i < particles.size(); i++) {
            int idx = random_choice(probabilities);
            resampled[i] = particles[idx];

            resampled[i].x     += rnd.gaussian(0, sigma2);
            resampled[i].y     += rnd.gaussian(0, sigma2);
            resampled[i].theta += rnd.gaussian(0, sigma2);
            resampled[i].theta = atan2(sin(resampled[i].theta), cos(resampled[i].theta));
        }
        return resampled;
    }
};