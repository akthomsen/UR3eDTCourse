import numpy as np

class MotionModel:

    def sync_time(self, distances, v_eff, a_eff):
        """Compute the synchronization time: the maximum natural travel time across all joints.

        arguments:
        - distances: array of per-joint distances to travel (radians)
        - v_eff: array of per-joint effective max velocities (rad/s)
        - a_eff: array of per-joint effective accelerations (rad/s^2)

        returns:
        - t_sync: the slowest joint's travel time (seconds)
        """
        d = np.asarray(distances)
        v = np.asarray(v_eff)
        a = np.asarray(a_eff)
        v_peak = np.minimum(v, np.sqrt(np.where(d < 1e-10, 0.0, a * d)))
        triangular = v_peak < v
        times = np.where(d < 1e-10, 0.0,
                        np.where(triangular, 2.0 * v_peak / a, d / v + v / a))
        return float(np.max(times))

    def sync_velocity(self, d, a, t_sync):
        """Find the v_max that makes a joint arrive in exactly t_sync seconds.
        Derived from trapezoidal time equation: T = d/v + v/a → v² - T·a·v + d·a = 0.

        arguments:
        - d: distance to travel (radians)
        - a: acceleration (rad/s^2)
        - t_sync: desired synchronization time (seconds)

        returns:
        - v_max: maximum velocity (rad/s) that achieves the synchronization time
        """
        if d < 1e-10 or t_sync < 1e-10:
            return 0.0
        # Solve the quadratic equation for v: v² - T·a·v + d·a = 0
        disc = (t_sync * a)**2 - 4.0 * d * a
        if disc < 0:
            return np.sqrt(a * d)              # triangular limit (numerical safety)
        return (t_sync * a - np.sqrt(disc)) / 2.0


    def simulate_joint_motion(
        self,
        q0,
        q_target,
        max_velocity_deg,
        acceleration_deg,
        dt,
        t_end,
        vel_scale,
        acc_scale
    ):
        n = len(q0)
        if len(vel_scale) != n:
            raise ValueError(f"vel_scale must have length {n}.")
        if len(acc_scale) != n:
            raise ValueError(f"acc_scale must have length {n}.")
        if len(q_target) != n:
            raise ValueError(f"q_target must have length {n}.")


        # Initialize joint start and target positions
        q = np.array(q0, dtype=float)
        q_tgt = np.array(q_target, dtype=float)
        qd = np.zeros(n)

        # Initialize simulation logs
        steps = int(np.ceil(t_end / dt)) + 1
        t = np.linspace(0, steps*dt, steps)[:steps]
        q_log = np.zeros((steps, n))
        qd_log = np.zeros((steps, n))
        qdd_log = np.zeros((steps, n))
        q_log[0] = q.copy()
        qd_log[0] = qd.copy()

        # Apply the per-joint scaling factors and convert limits to rad/s and rad/s^2
        a_eff = np.deg2rad(acceleration_deg) * np.asarray(acc_scale, dtype=float)
        v_eff = np.deg2rad(max_velocity_deg) * np.asarray(vel_scale, dtype=float)

        distances = np.abs(q_tgt - q)
        # Find the time where all joints are able to arrive at the target.
        t_sync = self.sync_time(distances, v_eff, a_eff)
        # Use the synchronization time to compute the effective velocity for each joint.
        v_eff = np.array([self.sync_velocity(distances[j], a_eff[j], t_sync) for j in range(n)])


        # Simulation loop
        for i in range(1, steps):
            qd_prev = qd.copy()
            for j in range(n):
                # Distance to target
                err = q_tgt[j] - q[j]
                # Current braking distance (per-joint acceleration)
                braking = (qd[j]**2) / (2.0 * a_eff[j]) if a_eff[j] > 0 else 0.0
                # Determine desired velocity
                if abs(err) <= braking + 1e-12:
                    # we are close, start braking
                    v_des = 0.0
                else:
                    v_des = v_eff[j] * np.sign(err)

                # Velocity change needed
                dv = v_des - qd[j]
                # Cap the velocity change considering the per-joint acceleration limits
                dv = np.clip(dv, -a_eff[j]*dt, a_eff[j]*dt)

                # Update velocity
                qd[j] = qd[j] + dv

                # Update position
                q[j] = q[j] + qd[j] * dt

            q_log[i] = q.copy()
            qd_log[i] = qd.copy()
            qdd_log[i] = (qd - qd_prev) / dt
        return t, q_log, qd_log, qdd_log
