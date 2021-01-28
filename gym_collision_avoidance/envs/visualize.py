import numpy as np
from gym_collision_avoidance.envs.util import find_nearest, rgba2rgb
import matplotlib.pyplot as plt
import matplotlib
import os
import matplotlib.patches as ptch
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
import glob
import imageio
from gym_collision_avoidance.envs.config import Config
import moviepy.editor as mp

from matplotlib.lines import Line2D
matplotlib.rcParams.update({'font.size': 24})

plt_colors = []
plt_colors.append([0.8500, 0.3250, 0.0980])  # orange
plt_colors.append([0.0, 0.4470, 0.7410])  # blue
plt_colors.append([0.4660, 0.6740, 0.1880])  # green
plt_colors.append([0.4940, 0.1840, 0.5560])  # purple
plt_colors.append([0.9290, 0.6940, 0.1250])  # yellow
plt_colors.append([0.3010, 0.7450, 0.9330])  # cyan
plt_colors.append([0.6350, 0.0780, 0.1840])  # chocolate
plt_colors.append([0.8, 0.0, 0.80])  # magenta
plt_colors.append([0.62, 0.62, 0.62])  # grey
plt_colors.append([0.2, 0.6, 0.1])  # light blue
plt_colors.append([1.0, 0.0, 0.0])  # red
plt_colors.append([0.0, 0.0, 0.0])  # red

def get_plot_save_dir(plot_save_dir, plot_policy_name, agents=None):
    if plot_save_dir is None:
        plot_save_dir = os.path.dirname(os.path.realpath(__file__)) + '/../logs/test_cases/'
        os.makedirs(plot_save_dir, exist_ok=True)
    if plot_policy_name is None:
        plot_policy_name = agents[0].policy.str

    collision_plot_dir = plot_save_dir + "/collisions/"
    os.makedirs(collision_plot_dir, exist_ok=True)

    deadlock_plot_dir = plot_save_dir + "/deadlocks/"
    os.makedirs(deadlock_plot_dir, exist_ok=True)

    base_fig_name = "{test_case}_{policy}_{num_agents}agents{step}.{extension}"
    return plot_save_dir, plot_policy_name, base_fig_name, collision_plot_dir, deadlock_plot_dir

def animate_episode(num_agents, plot_save_dir=None, plot_policy_name=None, test_case_index=0, agents=None):
    plot_save_dir, plot_policy_name, base_fig_name, collision_plot_dir, deadlock_plot_dir = get_plot_save_dir(plot_save_dir, plot_policy_name, agents)
    
    if not os.path.exists(plot_save_dir):
        os.makedirs(plot_save_dir)
        
    # Load all images of the current episode (each animation)
    fig_name = base_fig_name.format(
            policy=plot_policy_name,
            num_agents = num_agents,
            test_case = str(test_case_index).zfill(3),
            step="_*",
            extension='png')
    last_fig_name = base_fig_name.format(
            policy=plot_policy_name,
            num_agents = num_agents,
            test_case = str(test_case_index).zfill(3),
            step="",
            extension='png')
    all_filenames = plot_save_dir+fig_name
    last_filename = plot_save_dir+last_fig_name

    # Dump all those images into a gif (sorted by timestep)
    filenames = glob.glob(all_filenames)
    filenames.sort()
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))
        os.remove(filename)
    for i in range(10):
        images.append(imageio.imread(last_filename))

    # Save the gif in a new animations sub-folder
    animation_filename = base_fig_name.format(
            policy=plot_policy_name,
            num_agents = num_agents,
            test_case = str(test_case_index).zfill(3),
            step="",
            extension='gif')
    animation_save_dir = plot_save_dir+"animations/"
    os.makedirs(animation_save_dir, exist_ok=True)
    animation_filename = animation_save_dir+animation_filename
    imageio.mimsave(animation_filename, images)

    # convert .gif to .mp4
    #clip = mp.VideoFileClip(animation_filename)
    #clip.write_videofile(animation_filename[:-4]+".mp4")

def plot_episode(agents, obstacles, in_evaluate_mode,
    env_map=None, test_case_index=0, env_id=0,
    circles_along_traj=True, plot_save_dir=None, plot_policy_name=None,
    save_for_animation=False, limits=None, perturbed_obs=None,
    fig_size=(10,8), show=False, save=False):
    
    if max([agent.step_num for agent in agents]) == 0:
        return

    plot_save_dir, plot_policy_name, base_fig_name, collision_plot_dir, deadlock_plot_dir = get_plot_save_dir(plot_save_dir, plot_policy_name, agents)

    fig = plt.figure(env_id)
    fig.set_size_inches(fig_size[0], fig_size[1])

    plt.clf()

    ax = fig.add_subplot(1, 1, 1)

    # if env_map is not None:
    #     ax.imshow(env_map.static_map, extent=[-env_map.x_width/2., env_map.x_width/2., -env_map.y_width/2., env_map.y_width/2.], cmap=plt.cm.binary)

    if perturbed_obs is None:
        # Normal case of plotting
        max_time = draw_agents(agents, obstacles, circles_along_traj, ax)
    else:
        max_time = draw_agents(agents, obstacles, circles_along_traj, ax, last_index=-2)
        plot_perturbed_observation(agents, ax, perturbed_obs)

    # Label the axes
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')

    # plotting style (only show axis on bottom and left)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    legend_elements = []

    for agent in agents:
        if "RVO" in str(type(agent.policy)):
            leg = Line2D([0], [0], marker='o', color='w', label='RVO',
                              markerfacecolor=plt_colors[2], markersize=15)
        elif "MPC" in str(type(agent.policy)):
            leg = Line2D([0], [0], marker='o', color='w', label='MPC',
                   markerfacecolor=plt_colors[1], markersize=15)
        elif "GA3CCADRLPolicy" in str(type(agent.policy)):
            leg = Line2D([0], [0], marker='o', color='w', label='GA3C'+ str(agent.id),
                   markerfacecolor=plt_colors[8], markersize=15)
        else:
            leg = Line2D([0], [0], marker='o', color='w', label='Non cooperative',
                                          markerfacecolor=plt_colors[8], markersize=15)
        label_exists = False
        for legend in legend_elements:
            label_exists = label_exists or (legend.get_label() in  str(type(agent.policy)))
        if not label_exists:
            legend_elements.append(leg)
    """
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='GO-MPC',
                              markerfacecolor=plt_colors[7], markersize=15),
                       Line2D([0], [0], marker='o', color='w', label='Predicted Trajectory',
                              markerfacecolor=plt_colors[1], markersize=15),
                       Line2D([0], [0], marker='o', color='w', label='Guidance Network',
                              markerfacecolor=plt_colors[8], markersize=15),
                       Line2D([0], [0], marker='o', color='w', label='Cooperative Agent',
                              markerfacecolor=plt_colors[2], markersize=15)]
    """
    ax.legend(handles=legend_elements, loc='upper right')

    plt.draw()

    if limits is not None:
        xlim, ylim = limits
        plt.xlim(xlim)
        plt.ylim(ylim)
    else:
        ax.axis('equal')
        # hack to avoid zoom
        """
        x_pos = []
        y_pos = []
        if obstacles:
            for obstacle in obstacles:
                for pos in obstacle:
                    x_pos.append(pos[0])
                    y_pos.append(pos[1])
            plt.xlim([min(x_pos),max(x_pos)])
            plt.ylim([min(y_pos),max(y_pos)])
        else:
        """
        plt.xlim([-10.0,10.0])
        plt.ylim([-10.0,10.0])

    if in_evaluate_mode and save:
        fig_name = base_fig_name.format(
            policy=plot_policy_name,
            num_agents = len(agents),
            test_case = str(test_case_index).zfill(3),
            step="",
            extension='png')
        filename = plot_save_dir+fig_name
        plt.savefig(filename)

        if agents[0].in_collision:
            plt.savefig(collision_plot_dir+fig_name)

        if agents[0].ran_out_of_time:
            plt.savefig(deadlock_plot_dir + fig_name)

    if save_for_animation:
        try:
            fig_name = base_fig_name.format(
                policy=plot_policy_name,
                num_agents = len(agents),
                test_case = str(test_case_index).zfill(3),
                step="_"+"{:06.1f}".format(max_time),
                extension='png')
            filename = plot_save_dir+fig_name
            plt.savefig(filename)
        except:
            print("Error:")
            print(max_time)

    if show:
        plt.pause(0.0001)


def draw_agents(agents, obstacle, circles_along_traj, ax, last_index=-1):

    max_time = max([max(agent.global_state_history[:,0]) for agent in agents] + [1e-4])
    max_time_alpha_scalar = 1.2
    #plt.title(agents[0].policy.policy_name)
    other_plt_color = plt_colors[2]
    if max_time > 1e-4:
        # Add obstacles
        for i in range(len(obstacle)):
            ax.add_patch(plt.Polygon(np.array(obstacle[i]),ec=plt_colors[-1]))

        for i, agent in reversed(list(enumerate(agents))):

            # Plot line through agent trajectory
            if "RVO" in str(type(agent.policy)):
                plt_color = plt_colors[2]
            elif "MPC" in str(type(agent.policy)):
                plt_color = plt_colors[1]
            elif "GA3CCADRLPolicy" in str(type(agent.policy)):
                plt_color = plt_colors[1]
            else:
                plt_color = plt_colors[7]

            if Config.HOMOGENEOUS_TESTING:
                plt_color = plt_colors[i]

            t_final = agent.global_state_history[agent.step_num-1, 0]
            if circles_along_traj:
                plt.plot(agent.global_state_history[:agent.step_num-1, 1],
                         agent.global_state_history[:agent.step_num-1, 2],
                         color=plt_color, ls='-', linewidth=2)
                # Plot goal position
                plt.plot(agent.global_state_history[0, 3],
                         agent.global_state_history[0, 4],
                         color=plt_color, marker='+', markersize=20)
                if i == 0:
                    plt.plot(agent.next_goal[0],
                             agent.next_goal[1],
                             color=plt_colors[1], marker='*', markersize=20)

                # Display circle at agent pos every circle_spacing (nom 1.5 sec)
                circle_spacing = 0.4
                circle_times = np.arange(0.0, t_final,
                                         circle_spacing)
                if circle_times.size == 0:
                    continue
                _, circle_inds = find_nearest(agent.global_state_history[:agent.step_num-1,0],
                                              circle_times)
                for ind in circle_inds[0:]:
                    alpha = 1 - \
                            agent.global_state_history[ind, 0] / \
                            (max_time_alpha_scalar*max_time)
                    c = rgba2rgb(plt_color+[float(alpha)])
                    ax.add_patch(plt.Circle(agent.global_state_history[ind, 1:3],
                                 radius=agent.radius, fc=c, ec=plt_color,
                                 fill=True))

                if "Social" in str(type(agent.policy)):
                    for id,other_agent in enumerate(agents):
                        # Plot line through agent trajectory
                        if "RVO" in str(type(other_agent.policy)):
                            other_plt_color = plt_colors[2]
                        elif "MPC" in str(type(other_agent.policy)):
                            other_plt_color = plt_colors[1]
                        elif "GA3CCADRLPolicy" in str(type(other_agent.policy)):
                            other_plt_color = plt_colors[1]
                        else:
                            other_plt_color = plt_colors[10]

                        if Config.PLOT_PREDICTIONS:
                            for ind in range(agent.policy.FORCES_N):
                                alpha = 1 - ind*agent.policy.dt/agent.policy.FORCES_N
                                c = rgba2rgb(other_plt_color + [float(alpha)])
                                ax.add_patch(plt.Circle(agent.policy.all_predicted_trajectory[id,ind,:2]+agent.policy.all_predicted_trajectory[id,ind,2:4],
                                                        radius=agent.radius, fc=c, ec=other_plt_color,
                                                        fill=True))
                            if id == 0:
                                for ind in range(agent.policy.FORCES_N):
                                    alpha = 1 - ind * agent.policy.dt / agent.policy.FORCES_N
                                    c = rgba2rgb(plt_colors[7] + [float(alpha)])
                                    ax.add_patch(plt.Circle(agent.policy.guidance_traj[ind],
                                                            radius=agent.radius, fc=c, ec=plt_colors[7],
                                                            fill=True))
                        if id == 0:
                            for ind in range(agent.policy.FORCES_N):
                                alpha = 1 - ind*agent.policy.dt/agent.policy.FORCES_N
                                c = rgba2rgb(plt_colors[8] + [float(alpha)])
                                ax.add_patch(plt.Circle(agent.policy.predicted_traj[ind],
                                                        radius=agent.radius, fc=c, ec=plt_colors[8],
                                                        fill=True))

                # Display text of current timestamp every text_spacing (nom 1.5 sec)
                """
                text_spacing = 1.5
                text_times = np.arange(0.0, t_final,text_spacing)
                _, text_inds = find_nearest(agent.global_state_history[:agent.step_num-1,0],text_times)
                for ind in text_inds[1:]:
                    y_text_offset = 0.1
                    alpha = agent.global_state_history[ind, 0] / \
                        (max_time_alpha_scalar*max_time)
                    if alpha < 0.5:
                        alpha = 0.3
                    else:
                        alpha = 0.9
                    c = rgba2rgb(plt_color+[float(alpha)])
                    ax.text(agent.global_state_history[ind, 1]-0.15,
                            agent.global_state_history[ind, 2]+y_text_offset,
                            '%.1f' % agent.global_state_history[ind, 0], color=c)
                """
                if "Static" in str(type(agent.policy)):
                    obstacles = np.array(agent.sensors[1].static_obstacles_manager.obstacle)
                    for obs in obstacles:
                        ax.add_patch(plt.Polygon(obs, ec=plt_colors[-1],fill=False))
                # Also display circle at agent position at end of trajectory
                ind = agent.step_num-1
                alpha = 1 - \
                    agent.global_state_history[ind, 0] / \
                    (max_time_alpha_scalar*max_time)
                c = rgba2rgb(plt_color+[float(alpha)])
                ax.add_patch(plt.Circle(agent.global_state_history[ind, 1:3],
                             radius=agent.radius, fc=c, ec=plt_color))
                y_text_offset = 0.1
                ax.text(agent.global_state_history[ind, 1] - 0.15,
                        agent.global_state_history[ind, 2] + y_text_offset,
                        '%.1f' % agent.global_state_history[ind, 0],
                        color=plt_color)

                # if hasattr(agent.policy, 'deltaPos'):
                #     arrow_start = agent.global_state_history[ind, 1:3]
                #     arrow_end = agent.global_state_history[ind, 1:3] + (1.0/0.1)*agent.policy.deltaPos
                #     style="Simple,head_width=10,head_length=20"
                #     ax.add_patch(ptch.FancyArrowPatch(arrow_start, arrow_end, arrowstyle=style, color='black'))

            else:
                colors = np.zeros((agent.global_state_history.shape[0], 4))
                colors[:,:3] = plt_color
                colors[:, 3] = np.linspace(0.2, 1., agent.global_state_history.shape[0])
                colors = rgba2rgb(colors)

                plt.scatter(agent.global_state_history[:agent.global_state_history.shape[0], 1],
                         agent.global_state_history[:agent.global_state_history.shape[0], 2],
                         color=colors)

                # Also display circle at agent position at end of trajectory
                ind = agent.global_state_history.shape[0] + last_index
                alpha = 0.7
                c = rgba2rgb(plt_color+[float(alpha)])
                ax.add_patch(plt.Circle(agent.global_state_history[ind, 1:3],
                             radius=agent.radius, fc=c, ec=plt_color))
                # y_text_offset = 0.1
                # ax.text(agent.global_state_history[ind, 1] - 0.15,
                #         agent.global_state_history[ind, 2] + y_text_offset,
                #         '%.1f' % agent.global_state_history[ind, 0],
                #         color=plt_color)

        return max_time

def plot_perturbed_observation(agents, ax, perturbed_info):
    # This is hard-coded for 2 agent scenarios
    for i, agent in enumerate(agents):
        try:
            perturbed_obs = perturbed_info['perturbed_obs'][i]
        except:
            continue
        perturber = perturbed_info['perturber']
        other_agent_pos = agents[1].global_state_history[min(agent.step_num - 2, agents[1].step_num-1), 1:3]
        other_agent_perturbed_pos = agent.ego_pos_to_global_pos(perturbed_obs[4:6])
        rotation_angle = agent.ego_to_global_theta
        rotation_angle_deg = np.degrees(agent.ego_to_global_theta)
        other_agent_perturbed_lower_left_before_rotation = other_agent_perturbed_pos
        eps_lower_left_before_rotation = np.dot(np.array([[np.cos(rotation_angle), -np.sin(rotation_angle)], [np.sin(rotation_angle), np.cos(rotation_angle)]]), -perturber.epsilon_adversarial[0,4:6])
        other_agent_perturbed_lower_left_before_rotation = other_agent_perturbed_pos + eps_lower_left_before_rotation
        other_agent_lower_left_before_rotation = other_agent_pos + eps_lower_left_before_rotation
        ax.add_patch(plt.Circle(other_agent_perturbed_pos,
                     radius=agents[1].radius, fill=False, ec=plt_colors[-1]))
        
        if perturber.p == "inf":
            ax.add_patch(plt.Rectangle(other_agent_perturbed_lower_left_before_rotation,
                width=2*perturber.epsilon_adversarial[0,4],
                height=2*perturber.epsilon_adversarial[0,5],
                angle=rotation_angle_deg,
                fill=False,
                linestyle='--'))
            ax.add_patch(plt.Rectangle(other_agent_lower_left_before_rotation,
                width=2*perturber.epsilon_adversarial[0,4],
                height=2*perturber.epsilon_adversarial[0,5],
                angle=rotation_angle_deg,
                fill=False,
                linestyle=':'))

        ps = agent.ego_pos_to_global_pos(perturber.perturbation_steps[:,0,4:6])

        perturb_colors = np.zeros((perturber.perturbation_steps.shape[0]-1, 4))
        perturb_colors[:,:3] = plt_colors[-1]
        perturb_colors[:, 3] = np.linspace(0.2, 1.0, perturber.perturbation_steps.shape[0]-1)

        segs = np.reshape(np.hstack([ps[:-1], ps[1:]]), (perturber.perturbation_steps.shape[0]-1,2,2))[:-1]
        line_segments = LineCollection(segs, colors=perturb_colors, linestyle='solid')
        ax.add_collection(line_segments)

        plt.plot(other_agent_pos[0], other_agent_pos[1], 'x', color=plt_colors[i+1], zorder=4)
        plt.plot(other_agent_perturbed_pos[0], other_agent_perturbed_pos[1], 'x', color=plt_colors[-1], zorder=4)
