
import os
import sys
from app.src.utils.config import load_config, load_credentials, load_rollbar_token
from app.src.connector.connections import Connections
from app.src.fg_spp_data_queries import FGAccountStatus, SPPAccountStatus
import plotly.subplots as sp
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

class AccountInfo:  
    def __init__(self, st,account_sid,country,mcc):
        self.account_sid = account_sid
        self.country = country
        self.mcc = mcc
        self.st = st

    def presto_conn(self):    
        role = 'accsec-ai-playground'
        config = load_config(role)
        presto_username, presto_password = load_credentials(config["presto_creds"])
        conn = Connections()
        conn.presto_connector(presto_username, presto_password)

        return conn
    
     # Create plotly figure for traffic and CR
    def plot_traffic_and_blocks(self, verify_daily_traffic_acc_level, fds_daily_traffic_acc_level):
        # Create figure with secondary y-axis
        fig = sp.make_subplots(specs=[[{"secondary_y": True}]])

        # Add traffic line
        fig.add_trace(
            go.Scatter(
                x=verify_daily_traffic_acc_level.index,
                y=verify_daily_traffic_acc_level['daily_message_count'],
                name="Daily Traffic",
                line=dict(color='blue')
            ),
            secondary_y=False
        )

        # Add CR line on secondary axis
        fig.add_trace(
            go.Scatter(
                x=verify_daily_traffic_acc_level.index,
                y=verify_daily_traffic_acc_level['daily_avg_cr'],
                name="Conversion Rate",
                line=dict(color='red')
            ),
            secondary_y=True
        )

        # Update layout
        fig.update_layout(
            title="Daily Traffic and Conversion Rate",
            xaxis_title="Date",
            height=500
        )

        # Set y-axes titles
        fig.update_yaxes(title_text="Daily Traffic", secondary_y=False)
        fig.update_yaxes(title_text="Conversion Rate", secondary_y=True)

        # Display plot in Streamlit
        self.st.plotly_chart(fig, use_container_width=True)

        # Create stacked bar chart for blocks
        fig2 = go.Figure()

        # Add lines for each block type
        block_types = ['classic_fg', 'spp_block', 'risk_score_block', 'allowed_messages']
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']

        for block_type, color in zip(block_types, colors):
            fig2.add_trace(go.Scatter(
                x=fds_daily_traffic_acc_level.index,
                y=fds_daily_traffic_acc_level[block_type],
                name=block_type.replace('_', ' ').title(),
                line=dict(color=color)
            ))

        # Update layout for line chart
        fig2.update_layout(
            title="Daily Block Distribution",
            xaxis_title="Date", 
            yaxis_title="Number of Messages",
            height=500
        )

        # Display second plot in Streamlit
        self.st.plotly_chart(fig2, use_container_width=True)

    def get_account_info(self):
            days = '30'
            conn = self.presto_conn()
            fg_obj = FGAccountStatus(conn.presto_conn)
            spp_obj = SPPAccountStatus(conn.presto_conn)
            ## Check Account Active status
            account_active_status_df = fg_obj.is_account_active(self.account_sid)
            account_info_dict = account_active_status_df.set_index('account_sid').to_dict(orient='index')
            account_info = account_info_dict.get(self.account_sid, {})
            
            account_on_verify = account_info.get('account_on_verify', False)
            account_on_psms = account_info.get('account_on_psms', False)
            spp_enabled = account_info.get('spp_enabled', False)
            spp_shadow_enabled = account_info.get('spp_shadow_enabled', False)
            
            if account_on_verify and account_on_psms: 
                response = f"Account {self.account_sid}: is Active on both Verify and PSMS"
            elif account_on_verify: 
                response = f"Account {self.account_sid}: is only Active on Verify"
            elif account_on_psms: 
                response = f"Account {self.account_sid}: is only Active on PSMS"
            else:
                response = f"Account {self.account_sid}: is not Active"
                
            if spp_enabled:
                response += " SPP is also enabled on this Account."
            elif spp_shadow_enabled:
                response += " SPP is also enabled on this Account in Shadow Mode"       
            else:
                response += "\n\n" + "PSMS : SPP is not enabled" 

            self.st.write(response)
            ## CHECK FG IS ENABLED IN WHICH MODE. ALSO HOW MANY SERVICES ARE THERE AND ON WHICH SERVICE FG IS ENABLED.
            if account_on_verify:
                fg_enablement_status_df = fg_obj.get_fg_account_status(self.account_sid)
                acc_service_df = fg_enablement_status_df.drop_duplicates(subset=["service_sid"], keep="first")
                service_sid_count = fg_enablement_status_df['service_sid'].nunique()
                
                self.st.write(f'The Account {self.account_sid} has {service_sid_count} Service SID(s)')

                for status in ['enable', 'disable']:
                    df_filtered = acc_service_df[acc_service_df['fraud_guard'] == status]
                    if not df_filtered.empty:
                        fg_dataframe = df_filtered[['service_sid', 'fraud_guard', 'fraud_guard_mode']]
                        self.st.dataframe(fg_dataframe)
            
            ##### Get Data from Verify Table to get there overall CR and volume

            verify_daily_traffic = fg_obj.get_fg_account_data(self.account_sid,days = '30')
            verify_daily_traffic_acc_level = verify_daily_traffic.groupby(['data_load_date']).agg({'daily_message_count': 'sum', 'daily_avg_cr':'mean'})
            self.st.subheader("Verify Daily Traffic & CR")
            self.st.dataframe(verify_daily_traffic_acc_level)

            ##### Get Data from FDS RAW table - 
            fds_daily_traffic = fg_obj.get_fg_block_data(self.account_sid,days = '30')
            fds_daily_traffic_acc_level = fds_daily_traffic.groupby(['data_load_date']).agg({'total_traffic': 'sum', 
                                                                                            'classic_fg':'sum',
                                                                                            'spp_block':'sum',
                                                                                            'risk_score_block':'sum',
                                                                                            'fgl_safe_mcc_mnc':'sum',
                                                                                            'fgl_pass_safe_mcc_request':'sum',
                                                                                            'allowed_messages':'sum'
                                                                                            })
            self.st.subheader("FDS Daily Traffic & Block on Verify")

            self.st.dataframe(fds_daily_traffic_acc_level)
            ## Daily Traffic and Block Pattern wuth CR
        
            # Call the plotting function
            self.plot_traffic_and_blocks(verify_daily_traffic_acc_level, fds_daily_traffic_acc_level)

            # # Group by mcc and mnc for treemap
            # verify_traffic_by_mcc = verify_daily_traffic.groupby(['mcc', 'mnc']).agg({
            #                             'daily_message_count': 'sum',
            #                             'daily_avg_cr': 'mean'
            #                         }).reset_index()

            # fig = px.treemap(verify_traffic_by_mcc, 
            #                 path=['mcc', 'mnc'], 
            #                 values='daily_message_count',
            #                 color='daily_avg_cr',
            #                 color_continuous_scale='RdBu')
            
            # fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            # self.st.plotly_chart(fig, use_container_width=True)