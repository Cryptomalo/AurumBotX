import streamlit as st
import logging
from typing import Optional, Dict
from .code_fixer import CodeFixer

logger = logging.getLogger(__name__)

class TooltipComponent:
    def __init__(self):
        """Initialize the tooltip component with CodeFixer."""
        self.code_fixer = CodeFixer()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state for tooltips."""
        if 'tooltips' not in st.session_state:
            st.session_state.tooltips = {}
        if 'active_tooltip' not in st.session_state:
            st.session_state.active_tooltip = None

    def display_code_with_tooltips(self, code: str, errors: Optional[Dict] = None):
        """
        Display code in the Streamlit interface with interactive tooltips.
        
        Args:
            code: The code to display
            errors: Optional dictionary of errors mapped to line numbers
        """
        try:
            # Create a container for the code display
            code_container = st.container()
            
            with code_container:
                # Display code editor
                edited_code = st.text_area(
                    "Code Editor",
                    value=code,
                    height=300,
                    key="code_editor"
                )
                
                # Process any errors and generate tooltips
                if errors:
                    for line_num, error_info in errors.items():
                        tooltip = self.code_fixer.generate_tooltip(
                            f"Line {line_num}",
                            error_info
                        )
                        
                        # Store tooltip in session state
                        tooltip_key = f"tooltip_{line_num}"
                        st.session_state.tooltips[tooltip_key] = tooltip
                        
                        # Create a button that shows the tooltip
                        if st.button(f"Show suggestion for line {line_num}"):
                            st.session_state.active_tooltip = tooltip_key
                
                # Display active tooltip if any
                if st.session_state.active_tooltip:
                    st.info(st.session_state.tooltips[st.session_state.active_tooltip])
                    if st.button("Clear suggestion"):
                        st.session_state.active_tooltip = None

                return edited_code

        except Exception as e:
            logger.error(f"Error displaying code with tooltips: {str(e)}")
            st.error("Error displaying code editor with tooltips")
            return code

    def show_fix_suggestion(self, code: str, error_message: str):
        """
        Show fix suggestions for the given code and error.
        
        Args:
            code: The code with error
            error_message: The error message received
        """
        try:
            fixed_code, explanations = self.code_fixer.get_fix_suggestion(code, error_message)
            
            st.subheader("Suggested Fix")
            
            # Display the suggested fix
            col1, col2 = st.columns(2)
            
            with col1:
                st.code(fixed_code, language="python")
            
            with col2:
                for i, explanation in enumerate(explanations, 1):
                    st.write(f"{i}. {explanation}")
                    
                if st.button("Apply Fix"):
                    return fixed_code
                    
            return None
            
        except Exception as e:
            logger.error(f"Error showing fix suggestion: {str(e)}")
            st.error("Unable to generate fix suggestions at this time")
            return None
