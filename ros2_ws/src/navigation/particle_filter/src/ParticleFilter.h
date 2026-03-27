/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Instructions:
 * Write the code necessary to implement localization by particle filters.
 * Modify only the sections marked with the TODO comment.
 */
#include "particle_filter/ray_tracer.h"
#define FULL_NAME "Mercado Alejandre Mario Daniel"

class ParticleFilter
{
public:
    ParticleFilter() {}

    static std::vector<geometry_msgs::msg::Pose2D> get_initial_distribution(
        int N, float min_x, float max_x, float min_y, float max_y, float min_a, float max_a)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> particles(N);
        /*
         * TODO:
         * Generate a set of N particles (each particle represented by a Pose2D message)
         * with positions uniformly distributed within bounding box given by min_x, ..., max_a.
         * To generate uniformly distributed random numbers, you can use the funcion rnd.uniformReal(min, max)
         */
        for (size_t i = 0; i < particles.size(); i++)
        {
            particles[i].x = rnd.uniformReal(min_x, max_x);
            particles[i].y = rnd.uniformReal(min_y, max_y);
            particles[i].theta = rnd.uniformReal(min_a, max_a);
        }

        /*
         */
        return particles;
    }

    static void move_particles(std::vector<geometry_msgs::msg::Pose2D> &particles,
                               float delta_x, float delta_y, float delta_t, float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        /*
         * TODO:
         * Move each particle a displacement given by delta_x, delta_y and delta_t.
         * Displacement is given w.r.t. particles's frame, i.e., to calculate the new position for
         * each particle you need to rotate delta_x and delta_y, on Z axis, an angle theta_i, where theta_i
         * is the orientation of the i-th particle.
         * Add gaussian noise to each new position. Use sigma2 as variance.
         * You can use the function rnd.gaussian(mean, variance)
         */
        for (size_t i = 0; i < particles.size(); i++)
        {
            particles[i].x += delta_x * cos(particles[i].theta) - delta_y * sin(particles[i].theta) + rnd.gaussian(0, sigma2);
            particles[i].y += delta_x * sin(particles[i].theta) + delta_y * cos(particles[i].theta) + rnd.gaussian(0, sigma2);
            particles[i].theta += delta_t + rnd.gaussian(0, sigma2);
        }
    }

    static std::vector<sensor_msgs::msg::LaserScan> simulate_particle_scans(
        std::vector<geometry_msgs::msg::Pose2D> &particles,
        nav_msgs::msg::OccupancyGrid &map,
        sensor_msgs::msg::LaserScan &sensor_specs)
    {
        /*
         * TODO:
         * Review the code to simulate a laser scan for each particle given the set of particles and a static map.
         */
        std::vector<sensor_msgs::msg::LaserScan> simulated_scans(particles.size());
        for (size_t i = 0; i < particles.size(); i++)
        {
            geometry_msgs::msg::Pose sensor_pose;
            sensor_pose.position.x = particles[i].x;
            sensor_pose.position.y = particles[i].y;
            sensor_pose.orientation.w = cos(particles[i].theta / 2);
            sensor_pose.orientation.z = sin(particles[i].theta / 2);

            simulated_scans[i] = ray_tracer::simulateRangeScan(map, sensor_pose, sensor_specs);
        }
        return simulated_scans;
    }

    static std::vector<double> get_particle_similarities(
        std::vector<sensor_msgs::msg::LaserScan> &simulated_scans,
        sensor_msgs::msg::LaserScan &real_scan,
        int downsampling, float sigma2)
    {
        std::vector<double> similarities;
        similarities.resize(simulated_scans.size());

        for (size_t i = 0; i < simulated_scans.size(); i++)
        {
            double delta = 0.0;
            int M = 0; 

            
            for (size_t j = 0; j < simulated_scans[i].ranges.size(); j++)
            {
                float d_simulated = simulated_scans[i].ranges[j];
                float d_real = real_scan.ranges[j * downsampling];

                
                if (!std::isfinite(d_simulated) || !std::isfinite(d_real))
                    continue;

                delta += std::abs(d_real - d_simulated);
                M++;
            }

            
            if (M > 0)
                delta /= static_cast<double>(M);
            else
                delta = std::numeric_limits<double>::infinity();

            similarities[i] = std::exp(-delta / sigma2);
        }

        
        double total = 0.0;
        for (double s : similarities)
            total += s;

        if (total > 0.0)
            for (double &s : similarities)
                s /= total;
        else
            
            for (double &s : similarities)
                s = 1.0 / similarities.size();

        return similarities;
    }

    static int random_choice(std::vector<double> &probabilities)
    {
        random_numbers::RandomNumberGenerator rnd;
        /*
         * TODO:
         *
         * Write an algorithm to choice an integer in the range [0, N-1], with N, the length of 'probabilities'.
         * Probability of picking an integer 'i' is given by the corresponding probabilities[i] value.
         * Return the chosen integer.
         */
        std::vector<double> cumulative(probabilities.size());
        cumulative[0] = probabilities[0];
        for (size_t i = 1; i < probabilities.size(); i++)
            cumulative[i] = cumulative[i - 1] + probabilities[i];

        
        double r = rnd.uniformReal(0.0, 1.0);

        
        for (size_t i = 0; i < cumulative.size(); i++)
            if (r <= cumulative[i])
                return static_cast<int>(i);

        
        return static_cast<int>(probabilities.size() - 1);
    }

    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
        std::vector<geometry_msgs::msg::Pose2D> &particles, std::vector<double> &probabilities, float sigma2)
    {
        random_numbers::RandomNumberGenerator rnd;
        std::vector<geometry_msgs::msg::Pose2D> resampled_particles(particles.size());

        for (size_t i = 0; i < resampled_particles.size(); i++)
        {
            
            int chosen = random_choice(probabilities);

            resampled_particles[i].x = particles[chosen].x + rnd.gaussian(0, sigma2);
            resampled_particles[i].y = particles[chosen].y + rnd.gaussian(0, sigma2);
            resampled_particles[i].theta = particles[chosen].theta + rnd.gaussian(0, sigma2);
        }

        return resampled_particles;
    }
};